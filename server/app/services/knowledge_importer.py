 from app.utils.logger import logger
 class KnowledgeImporter:
     def import_file(self, file_path, parse_mode="chunk"):
         logger.info(f"Importing: {file_path} ({parse_mode})")
         return {"status": "success", "chunks": 0}
