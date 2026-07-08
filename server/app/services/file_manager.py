 import os
 from app.utils.logger import logger
 class FileManager:
     def __init__(self, storage_dir="./data/knowledge_store"):
         self.storage_dir = storage_dir
         os.makedirs(self.storage_dir, exist_ok=True)
     def save_upload(self, filename, content):
         path = os.path.join(self.storage_dir, filename)
         with open(path, "wb") as f:
             f.write(content)
         return path
     def delete_file(self, path):
         if os.path.exists(path):
             os.remove(path)
             return True
         return False
