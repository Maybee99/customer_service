"""
Knowledge base import service.
Orchestrates the full pipeline: parse → chunk → embed → store → index.
"""
import os
import hashlib
import threading

from ..rag.embeddings import EmbeddingService
from ..rag.milvus_store import MilvusStore
from ..rag.bm25_search import BM25Search
from ..services.document_parser import DocumentParser
from ..services.text_chunker import TextChunker
from ..models.database import SessionLocal
from ..models.knowledge_file import KnowledgeFile
from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()

# File lock for BM25 rebuilds (avoids concurrent rebuilds)
_bm25_lock = threading.Lock()


class KnowledgeImporter:
    """Full knowledge import pipeline."""

    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embeddings = EmbeddingService()
        self.milvus = MilvusStore()
        self.bm25 = BM25Search()

    # ── Public API ──────────────────────────────────────────

    def process_file(self, file_id: int, file_path: str) -> dict:
        """Run the full import pipeline for an uploaded file.

        Called as a background task after the file is saved and the
        database record is created.

        Returns:
            dict with keys: status, chunk_count, error_message
        """
        db = SessionLocal()
        try:
            record = db.query(KnowledgeFile).filter(
                KnowledgeFile.id == file_id
            ).first()
            if not record:
                return {"status": "error", "error_message": "File record not found"}

            # ① Update status
            record.status = "processing"
            db.commit()

            file_type = record.file_type
            original_name = record.original_filename
            category = getattr(record, 'category', '') or ''

            logger.info(f"[KnowledgeImporter] Processing file #{file_id}: "
                         f"{original_name} (type={file_type}, category={category})")

            # ② Parse document → text
            try:
                text = self.parser.parse_file(file_path, file_type)
            except (ValueError, FileNotFoundError) as e:
                self._fail(db, record, str(e))
                return {"status": "failed", "error_message": str(e)}
            except Exception as e:
                self._fail(db, record, f"文档解析失败: {str(e)[:500]}")
                return {"status": "failed", "error_message": f"解析失败: {str(e)[:200]}"}

            if not text or not text.strip():
                self._fail(db, record, "文档无文字内容")
                return {"status": "failed", "error_message": "文档无文字内容"}

            # ③ Chunk text
            chunks_meta = self.chunker.chunk_with_metadata(
                text, source_file=original_name, category=category
            )
            if not chunks_meta:
                self._fail(db, record, "文档分块后无有效内容")
                return {"status": "failed", "error_message": "文档分块后无有效内容"}

            logger.info(f"[KnowledgeImporter] Got {len(chunks_meta)} chunks")

            # ④ Generate embeddings (batch of 10)
            contents = [c["content"] for c in chunks_meta]
            try:
                embeddings = self._embed_batch(contents)
            except Exception as e:
                self._fail(db, record, f"向量生成失败: {str(e)[:200]}")
                return {"status": "failed", "error_message": f"向量生成失败: {str(e)[:200]}"}

            if len(embeddings) != len(contents):
                self._fail(db, record, "向量生成数量与分块数不一致")
                return {"status": "failed", "error_message": "向量生成数量不一致"}

            # ⑤ Insert into Milvus
            file_hash = record.file_hash
            source_files = [c["source_file"] for c in chunks_meta]
            categories = [c["category"] for c in chunks_meta]
            chunk_indices = [c["chunk_index"] for c in chunks_meta]
            file_hashes = [file_hash] * len(chunks_meta)

            try:
                self.milvus.insert(
                    embeddings=embeddings,
                    contents=contents,
                    source_files=source_files,
                    categories=categories,
                    chunk_indices=chunk_indices,
                    file_hashes=file_hashes,
                )
            except Exception as e:
                self._fail(db, record, f"向量存储失败: {str(e)[:200]}")
                return {"status": "failed", "error_message": f"向量存储失败: {str(e)[:200]}"}

            # ⑥ Rebuild BM25 index
            try:
                self.rebuild_bm25_index()
            except Exception as e:
                logger.warning(f"[KnowledgeImporter] BM25 rebuild failed (non-fatal): {e}")

            # ⑦ Update status → ready
            record.status = "ready"
            record.chunk_count = len(chunks_meta)
            db.commit()

            logger.info(f"[KnowledgeImporter] File #{file_id} ready: "
                         f"{len(chunks_meta)} chunks")

            return {
                "status": "ready",
                "chunk_count": len(chunks_meta),
            }

        except Exception as e:
            logger.error(f"[KnowledgeImporter] Unexpected error: {e}")
            try:
                self._fail(db, db.query(KnowledgeFile).get(file_id), f"未知错误: {str(e)[:500]}")
            except Exception:
                pass
            return {"status": "failed", "error_message": str(e)[:500]}
        finally:
            db.close()

    def delete_knowledge(self, file_hash: str) -> bool:
        """Remove all chunks for a file from Milvus and rebuild BM25."""
        try:
            self.milvus.delete_by_file_hash(file_hash)
            logger.info(f"[KnowledgeImporter] Deleted Milvus chunks: hash={file_hash}")
        except Exception as e:
            logger.error(f"[KnowledgeImporter] Milvus delete failed: {e}")
            return False

        try:
            self.rebuild_bm25_index()
        except Exception as e:
            logger.warning(f"[KnowledgeImporter] BM25 rebuild after delete failed: {e}")

        return True

    def rebuild_bm25_index(self) -> int:
        """Rebuild BM25 index from all documents in Milvus.

        Thread-safe: uses a lock to avoid concurrent rebuilds.
        Returns the number of documents indexed.
        """
        with _bm25_lock:
            import pickle
            from rank_bm25 import BM25Okapi

            # Fetch all documents from Milvus
            all_docs = self._fetch_all_milvus_docs()
            if not all_docs:
                logger.warning("[KnowledgeImporter] No docs in Milvus, skipping BM25 rebuild")
                return 0

            logger.info(f"[KnowledgeImporter] Building BM25 index from {len(all_docs)} docs")

            # Tokenize (BM25Okapi expects list of token lists)
            tokenized = [self._tokenize(doc["content"]) for doc in all_docs]
            bm25 = BM25Okapi(tokenized)

            # Save
            index_path = os.path.join(settings.data_dir, "bm25_index.pkl")
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            with open(index_path, "wb") as f:
                pickle.dump({"bm25": bm25, "documents": all_docs}, f)

            # Reload into the runtime BM25Search instance
            self.bm25.bm25 = bm25
            self.bm25.documents = all_docs

            logger.info(f"[KnowledgeImporter] BM25 index saved: {len(all_docs)} docs")
            return len(all_docs)

    # ── Internal helpers ────────────────────────────────────

    @staticmethod
    def _fail(db, record, message: str):
        """Mark a file record as failed."""
        if record:
            record.status = "failed"
            record.error_message = message[:1000]
            db.commit()
        logger.error(f"[KnowledgeImporter] FAILED: {message}")

    def _embed_batch(self, texts: list, batch_size: int = 10) -> list:
        """Generate embeddings in batches to avoid API rate limits."""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"[KnowledgeImporter] Embedding batch {i // batch_size + 1}/"
                         f"{(len(texts) - 1) // batch_size + 1} ({len(batch)} texts)")
            all_embeddings.extend(self.embeddings.embed_documents(batch))
        return all_embeddings

    def _fetch_all_milvus_docs(self) -> list:
        """Fetch all documents from Milvus for BM25 rebuild.

        Uses paginated queries to respect Milvus's 16384 result window limit.
        """
        try:
            all_docs = []
            offset = 0
            batch_size = 5000  # Safe batch size well under 16384 limit
            while True:
                results = self.milvus.client.query(
                    collection_name=self.milvus.collection_name,
                    filter="id >= 0",
                    output_fields=["content", "source_file", "category",
                                  "chunk_index", "file_hash"],
                    limit=batch_size,
                    offset=offset,
                )
                if not results:
                    break
                for hit in results:
                    all_docs.append({
                        "content": hit.get("content", ""),
                        "source_file": hit.get("source_file", ""),
                        "category": hit.get("category", ""),
                        "chunk_index": hit.get("chunk_index", 0),
                        "file_hash": hit.get("file_hash", ""),
                    })
                if len(results) < batch_size:
                    break
                offset += batch_size
            return all_docs
        except Exception as e:
            logger.error(f"[KnowledgeImporter] Failed to fetch Milvus docs: {e}")
            return []

    @staticmethod
    def _tokenize(text: str) -> list:
        """Tokenize text for BM25 indexing.

        Uses shared jieba-based tokenizer for consistent tokenization
        between index build and query time.
        """
        from ..rag.tokenizer import tokenize as _tokenize_fn
        return _tokenize_fn(text, remove_stopwords=True)


# Module-level convenience
importer = KnowledgeImporter()
