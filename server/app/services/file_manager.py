import os
from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()


class FileManager:
    """Manage uploaded knowledge base files on disk."""

    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.join(settings.data_dir, "knowledge_store")
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"[FileManager] Storage dir: {self.storage_dir}")

    def save_upload(self, filename: str, content: bytes) -> str:
        """Save an uploaded file and return the full path."""
        path = os.path.join(self.storage_dir, filename)
        with open(path, "wb") as f:
            f.write(content)
        logger.info(f"[FileManager] Saved: {filename} ({len(content)} bytes)")
        return path

    def delete_file(self, path: str) -> bool:
        """Delete a file from disk."""
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"[FileManager] Deleted: {path}")
            return True
        return False
