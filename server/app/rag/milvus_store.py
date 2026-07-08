from typing import List, Dict, Any, Optional
from pymilvus import MilvusClient, DataType
from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()


class MilvusStore:
    """Milvus vector database wrapper using MilvusClient API"""

    def __init__(self):
        self.host = settings.milvus_host
        self.port = settings.milvus_port
        self.collection_name = settings.milvus_collection
        self.dim = settings.milvus_dim
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = MilvusClient(uri=f"http://{self.host}:{self.port}")
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            self._ensure_collection()
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _ensure_collection(self):
        if self.client.has_collection(self.collection_name):
            logger.info(f"Loaded existing collection: {self.collection_name}")
            return

        schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=False)
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=self.dim)
        schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=8192)
        schema.add_field(field_name="source_file", datatype=DataType.VARCHAR, max_length=500)
        schema.add_field(field_name="category", datatype=DataType.VARCHAR, max_length=100)
        schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
        schema.add_field(field_name="file_hash", datatype=DataType.VARCHAR, max_length=64)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="IP",
            params={"nlist": 128}
        )

        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params
        )
        logger.info(f"Created collection: {self.collection_name} (dim={self.dim})")

    def insert(self, embeddings: List[List[float]], contents: List[str],
               source_files: List[str], categories: List[str],
               chunk_indices: List[int], file_hashes: List[str]):
        """Insert document chunks into Milvus.

        Normalizes embeddings before insertion so IP metric behaves
        like COSINE similarity.
        """
        import math
        rows = []
        for i in range(len(contents)):
            emb = embeddings[i]
            # L2-normalize: IP on normalized vectors = COSINE
            norm = math.sqrt(sum(x * x for x in emb))
            if norm > 0:
                emb = [x / norm for x in emb]
            rows.append({
                "embedding": emb,
                "content": contents[i],
                "source_file": source_files[i],
                "category": categories[i],
                "chunk_index": chunk_indices[i],
                "file_hash": file_hashes[i],
            })
        self.client.insert(collection_name=self.collection_name, data=rows)
        logger.info(f"Inserted {len(contents)} chunks into Milvus")

    def search(self, query_embedding: List[float], top_k: int = 5,
               category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional category filter.

        Normalizes the query vector so IP ≈ COSINE on normalized vectors.
        Uses nprobe=32 to search 25% of the IVF clusters (was 10 → 7.8%).
        """
        # Normalize query embedding for stable IP scores
        import math
        norm = math.sqrt(sum(x * x for x in query_embedding))
        if norm > 0:
            query_embedding = [x / norm for x in query_embedding]

        filter_expr = None
        if category:
            filter_expr = f'category == "{category}"'

        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k,
            search_params={"metric_type": "IP", "params": {"nprobe": 32}},
            output_fields=["content", "source_file", "category", "chunk_index", "file_hash"],
            filter=filter_expr,
        )

        docs = []
        for hits in results:
            for hit in hits:
                docs.append({
                    "content": hit["entity"].get("content"),
                    "source_file": hit["entity"].get("source_file"),
                    "category": hit["entity"].get("category"),
                    "chunk_index": hit["entity"].get("chunk_index"),
                    "file_hash": hit["entity"].get("file_hash", ""),
                    "score": hit["distance"],
                    "type": "milvus",
                })
        return docs

    def delete_by_file_hash(self, file_hash: str):
        """Delete all chunks belonging to a specific file"""
        expr = f'file_hash == "{file_hash}"'
        self.client.delete(collection_name=self.collection_name, filter=expr)
        logger.info(f"Deleted chunks with file_hash={file_hash}")

    def count(self) -> int:
        """Get total number of entities in collection"""
        stats = self.client.get_collection_stats(collection_name=self.collection_name)
        return stats.get("row_count", 0)

    def drop_collection(self):
        """Drop the collection (for testing)"""
        self.client.drop_collection(collection_name=self.collection_name)
        logger.info(f"Dropped collection: {self.collection_name}")

    def close(self):
        self.client.close()
        logger.info("Disconnected from Milvus")

