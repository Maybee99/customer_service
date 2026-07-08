 from typing import List, Dict, Any, Optional
 from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
 from app.config import get_settings
 from app.utils.logger import logger

 settings = get_settings()


 class MilvusStore:
     """Milvus vector database wrapper for knowledge base storage and retrieval"""

     def __init__(self):
         self.host = settings.milvus_host
         self.port = settings.milvus_port
         self.collection_name = settings.milvus_collection
         self.dim = settings.milvus_dim
         self.collection = None
         self._connect()

     def _connect(self):
         try:
             connections.connect(host=self.host, port=self.port)
             logger.info(f"Connected to Milvus at {self.host}:{self.port}")
             self._ensure_collection()
         except Exception as e:
             logger.error(f"Failed to connect to Milvus: {e}")
             raise

     def _ensure_collection(self):
         if utility.has_collection(self.collection_name):
             self.collection = Collection(self.collection_name)
             self.collection.load()
             logger.info(f"Loaded existing collection: {self.collection_name}")
             return

         schema = CollectionSchema([
             FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
             FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
             FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
             FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=500),
             FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
             FieldSchema(name="chunk_index", dtype=DataType.INT64),
             FieldSchema(name="file_hash", dtype=DataType.VARCHAR, max_length=64),
         ])

         self.collection = Collection(self.collection_name, schema)
         index_params = {"metric_type": "IP", "index_type": "IVFFLAT", "params": {"nlist": 128}}
         self.collection.create_index("embedding", index_params)
         self.collection.load()
         logger.info(f"Created collection: {self.collection_name} (dim={self.dim})")

     def insert(self, embeddings: List[List[float]], contents: List[str],
                source_files: List[str], categories: List[str],
                chunk_indices: List[int], file_hashes: List[str]):
         """Insert document chunks into Milvus"""
         entities = [
             [embeddings],
             contents,
             source_files,
             categories,
             chunk_indices,
             file_hashes,
         ]
         # Transpose: list of columns -> list of rows
         rows = []
         for i in range(len(contents)):
             rows.append({
                 "embedding": embeddings[i],
                 "content": contents[i],
                 "source_file": source_files[i],
                 "category": categories[i],
                 "chunk_index": chunk_indices[i],
                 "file_hash": file_hashes[i],
             })
         self.collection.insert(rows)
         self.collection.flush()
         logger.info(f"Inserted {len(contents)} chunks into Milvus")

     def search(self, query_embedding: List[float], top_k: int = 5,
                category: Optional[str] = None) -> List[Dict[str, Any]]:
         """Search for similar vectors with optional category filter"""
         expr = None
         if category:
             expr = f'category == "{category}"'

         results = self.collection.search(
             data=[query_embedding],
             anns_field="embedding",
             param={"metric_type": "IP", "params": {"nprobe": 10}},
             limit=top_k,
             expr=expr,
             output_fields=["content", "source_file", "category", "chunk_index"],
         )

         docs = []
         for hits in results:
             for hit in hits:
                 docs.append({
                     "content": hit.entity.get("content"),
                     "source_file": hit.entity.get("source_file"),
                     "category": hit.entity.get("category"),
                     "chunk_index": hit.entity.get("chunk_index"),
                     "score": hit.score,
                     "type": "milvus",
                 })
         return docs

     def delete_by_file_hash(self, file_hash: str):
         """Delete all chunks belonging to a specific file"""
         expr = f'file_hash == "{file_hash}"'
         self.collection.delete(expr)
         logger.info(f"Deleted chunks with file_hash={file_hash}")

     def count(self) -> int:
         """Get total number of entities in collection"""
         self.collection.flush()
         return self.collection.num_entities

     def drop_collection(self):
         """Drop the collection (for testing)"""
         self.collection.release()
         utility.drop_collection(self.collection_name)
         logger.info(f"Dropped collection: {self.collection_name}")

     def close(self):
         connections.disconnect(alias="default")
         logger.info("Disconnected from Milvus")
