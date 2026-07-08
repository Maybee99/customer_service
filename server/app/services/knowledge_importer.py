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
from ..models.knowledge_image import KnowledgeImage
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
                         f"{original_name} (type={file_type}, category={category}) "
                         f"path={file_path}")

            # ② Parse document → text (or image-based for low-text PDFs)
            chunks_meta = None
            image_pages = None

            if file_type == 'pdf':
                # Check text density — route image-heavy PDFs to Qwen-VL
                try:
                    from ..services.image_parser import ImageParser
                    img_parser = ImageParser()
                    _, text_density = img_parser.get_text_density(file_path)
                    logger.info(
                        f"[KnowledgeImporter] Text density: {text_density:.0f} "
                        f"chars/page (threshold=100)"
                    )
                except Exception as e:
                    logger.warning(
                        f"[KnowledgeImporter] Density check failed ({e}), "
                        f"falling back to text parsing"
                    )
                    text_density = 999  # Can't check → assume text-heavy

                # Threshold: < 100 chars/page → screenshot-style PDF
                if text_density < 100:
                    logger.info(
                        f"[KnowledgeImporter] Low text density ({text_density:.0f} "
                        f"chars/page) → using Qwen-VL image parsing"
                    )
                    try:
                        progress_cb = lambda pct, step: self._update_progress(
                            db, record, pct, step
                        )
                        image_pages = img_parser.parse_pdf(
                            file_path, file_hash=record.file_hash,
                            file_id=record.id,
                            progress_callback=progress_cb,
                        )
                        if image_pages:
                            chunks_meta = [
                                {
                                    "content": p["text"],
                                    "chunk_index": p["page_num"],
                                    "source_file": original_name,
                                    "category": category,
                                }
                                for p in image_pages
                            ]
                            # Set image info on record
                            record.image_count = len(image_pages)
                    except Exception as e:
                        logger.error(f"[KnowledgeImporter] Image parsing failed: {e}")
                        # Fall through to text parsing

            # Normal text path (fallback or text-heavy PDF)
            if chunks_meta is None:
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

                self._update_progress(db, record, 25, "文档解析完成")

                # ③ Chunk text
                chunks_meta = self.chunker.chunk_with_metadata(
                    text, source_file=original_name, category=category
                )
            if not chunks_meta:
                self._fail(db, record, "文档分块后无有效内容")
                return {"status": "failed", "error_message": "文档分块后无有效内容"}

            logger.info(f"[KnowledgeImporter] Got {len(chunks_meta)} chunks")
            self._update_progress(db, record, 40, "文档分块完成")

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

            self._update_progress(db, record, 60, "向量生成完成")

            # ⑤ Delete old chunks before inserting new ones
            file_hash = record.file_hash
            try:
                self.milvus.delete_by_file_hash(file_hash)
                logger.info(f"[KnowledgeImporter] Cleaned old chunks for hash={file_hash[:16]}")
            except Exception as e:
                logger.warning(f"[KnowledgeImporter] Clean old chunks failed: {e}")

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

            self._update_progress(db, record, 80, "向量存储完成")

            # ⑥ Rebuild BM25 index
            try:
                self.rebuild_bm25_index()
            except Exception as e:
                logger.warning(f"[KnowledgeImporter] BM25 rebuild failed (non-fatal): {e}")

            self._update_progress(db, record, 95, "索引构建完成")

            # ⑦ Update status → ready
            record.status = "ready"
            record.progress = 100
            record.progress_step = "处理完成"
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

    def delete_knowledge(self, file_hash: str, original_filename: str = "") -> bool:
        """Remove all chunks for a file from Milvus, delete page images, rebuild BM25."""
        try:
            self.milvus.delete_by_file_hash(file_hash)
            logger.info(f"[KnowledgeImporter] Deleted Milvus chunks: hash={file_hash}")
        except Exception as e:
            logger.error(f"[KnowledgeImporter] Milvus delete failed: {e}")
            return False

        # ── Delete page images (generated by ImageParser) ──
        self._delete_page_images(file_hash)

        try:
            self.rebuild_bm25_index()
        except Exception as e:
            logger.warning(f"[KnowledgeImporter] BM25 rebuild after delete failed: {e}")

        return True

    @staticmethod
    def _delete_page_images(file_hash: str):
        """Delete page images belonging to a specific file from disk and DB.

        ImageParser saves images as: data/images/{file_hash}_p{N}.png
        This method removes all matching images from disk and the
        knowledge_images table.
        """
        import glob
        image_dir = os.path.join(settings.data_dir, "images")
        deleted = 0

        # ── Delete from disk ──
        if os.path.isdir(image_dir):
            patterns = [
                os.path.join(image_dir, f"{file_hash}_p*.png"),
                os.path.join(image_dir, f"{file_hash[:16]}_p*.png"),
                os.path.join(image_dir, f"{file_hash[:32]}_p*.png"),
            ]
            for pattern in patterns:
                for img_path in glob.glob(pattern):
                    try:
                        os.remove(img_path)
                        deleted += 1
                    except OSError as e:
                        logger.warning(f"[KnowledgeImporter] Failed to delete image {img_path}: {e}")

        # ── Delete from knowledge_images table ──
        try:
            db2 = SessionLocal()
            count = db2.query(KnowledgeImage).filter(
                KnowledgeImage.file_hash == file_hash
            ).delete()
            db2.commit()
            if count > 0:
                logger.info(f"[KnowledgeImporter] Deleted {count} image metadata "
                            f"records for hash={file_hash[:16]}")
        except Exception as e:
            logger.warning(f"[KnowledgeImporter] Failed to delete image metadata: {e}")
        finally:
            db2.close()

        if deleted > 0:
            logger.info(f"[KnowledgeImporter] Deleted {deleted} page images from "
                        f"disk for hash={file_hash[:16]}")

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

    # ── Progress tracking ───────────────────────────────────

    @staticmethod
    def _update_progress(db, record, progress: int, step: str):
        """Update file processing progress visible to the frontend."""
        if record:
            record.progress = progress
            record.progress_step = step
            db.commit()

    # ── Internal helpers ────────────────────────────────────

    @staticmethod
    def _fail(db, record, message: str):
        """Mark a file record as failed."""
        if record:
            record.status = "failed"
            record.progress = 0
            record.progress_step = f"失败: {message[:60]}"
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
