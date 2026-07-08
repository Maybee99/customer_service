"""
Knowledge base API — upload, list, delete, reindex documents.
"""
import os
import hashlib
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Query, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.knowledge_file import KnowledgeFile
from ..services.file_manager import FileManager
from ..services.knowledge_importer import KnowledgeImporter
from ..config import get_settings
from ..utils.logger import logger

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

settings = get_settings()
file_manager = FileManager()
importer = KnowledgeImporter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_CATEGORIES = {"hr_policy", "finance", "it_support", "company_rules", ""}


# ── Upload ─────────────────────────────────────────────────

@router.post("/upload", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(default=""),
    parse_mode: str = Form(default="chunk"),
    db: Session = Depends(get_db),
):
    """Upload a PDF or Word document for RAG ingestion.

    The file is saved immediately and processed asynchronously.
    Poll GET /files/{id} for status updates.
    """
    # ── Validate file extension ──
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}，仅支持 PDF (.pdf) 和 Word (.docx) 文档",
        )

    # ── Validate category ──
    if category and category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的分类 '{category}'，可选: {', '.join(sorted(ALLOWED_CATEGORIES - {''}))}",
        )

    # ── Read file content ──
    content = await file.read()

    # ── Validate size ──
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="文件为空")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小 {file_size / 1024 / 1024:.1f}MB 超过限制（最大 50MB）",
        )

    # ── Compute hash & check duplicate ──
    file_hash = hashlib.sha256(content).hexdigest()
    existing = db.query(KnowledgeFile).filter(
        KnowledgeFile.file_hash == file_hash
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "文件已存在（SHA256 重复）",
                "existing": {
                    "id": existing.id,
                    "original_filename": existing.original_filename,
                    "status": existing.status,
                },
            },
        )

    # ── Save file to disk ──
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = file_manager.save_upload(safe_name, content)

    # ── Create database record ──
    file_type = ext.lstrip(".")
    record = KnowledgeFile(
        original_filename=file.filename,
        file_type=file_type,
        file_hash=file_hash,
        file_size=file_size,
        category=category,
        parse_mode=parse_mode if parse_mode in ("chunk", "qa") else "chunk",
        status="processing",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(f"[Knowledge API] Uploaded: id={record.id}, name={file.filename},"
                f" size={file_size}, category={category}")

    # ── Enqueue background processing ──
    background_tasks.add_task(importer.process_file, record.id, file_path)

    return {
        "id": record.id,
        "original_filename": record.original_filename,
        "file_type": record.file_type,
        "file_size": record.file_size,
        "category": record.category,
        "parse_mode": record.parse_mode,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


# ── List files ─────────────────────────────────────────────

@router.get("/files")
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List uploaded knowledge files with pagination and optional filters."""
    query = db.query(KnowledgeFile)

    if category:
        query = query.filter(KnowledgeFile.category == category)
    if status:
        query = query.filter(KnowledgeFile.status == status)

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    records = (
        query.order_by(KnowledgeFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    files = [_serialize_file(r) for r in records]

    return {
        "files": files,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ── File detail + progress ────────────────────────────────

@router.get("/files/{file_id}/progress")
async def get_file_progress(file_id: int, db: Session = Depends(get_db)):
    """Poll file processing progress (for upload progress bar)."""
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")
    return {
        "id": record.id,
        "status": record.status,
        "progress": record.progress or 0,
        "progress_step": record.progress_step or "",
        "error_message": record.error_message,
    }


# ── File detail ────────────────────────────────────────────

@router.get("/files/{file_id}")
async def get_file(file_id: int, db: Session = Depends(get_db)):
    """Get a single file's details."""
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")
    return _serialize_file(record)


# ── View / Download file ──────────────────────────────────

@router.get("/download/{filename:path}")
async def download_file(filename: str):
    """View (PDF inline) or download an uploaded knowledge base file."""
    storage_dir = file_manager.storage_dir
    for fname in os.listdir(storage_dir):
        full_path = os.path.join(storage_dir, fname)
        if not os.path.isfile(full_path):
            continue
        if fname.endswith("_" + filename) or fname == filename:
            # PDF → show inline in browser; others → download
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.pdf':
                return FileResponse(full_path, media_type="application/pdf")
            elif ext in ('.docx', '.doc'):
                return FileResponse(
                    full_path,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    filename=filename,
                )
            else:
                return FileResponse(full_path, filename=filename)

    raise HTTPException(status_code=404, detail="文件不存在或已从磁盘删除")


# ── Delete file ────────────────────────────────────────────

@router.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Delete a file and all its chunks from the knowledge base."""
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_hash = record.file_hash
    filename = record.original_filename
    chunk_count = record.chunk_count

    # ① Delete from Milvus, page images & rebuild BM25
    ok = importer.delete_knowledge(file_hash, original_filename=filename)

    # ② Delete from disk (best-effort, find by original filename in storage dir)
    try:
        for fname in os.listdir(file_manager.storage_dir):
            if filename in fname and os.path.isfile(
                os.path.join(file_manager.storage_dir, fname)
            ):
                os.remove(os.path.join(file_manager.storage_dir, fname))
                break
    except Exception as e:
        logger.warning(f"[Knowledge API] Disk cleanup failed: {e}")

    # ③ Delete from MySQL
    db.delete(record)
    db.commit()

    logger.info(f"[Knowledge API] Deleted file #{file_id}: {filename}")

    return {
        "status": "deleted",
        "deleted_chunks": chunk_count,
        "file_id": file_id,
        "original_filename": filename,
        "milvus_cleaned": ok,
    }


# ── Reindex ────────────────────────────────────────────────

@router.post("/files/{file_id}/reindex", status_code=202)
async def reindex_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Re-process a previously failed file."""
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")

    if record.status not in ("failed", "ready"):
        raise HTTPException(
            status_code=400,
            detail=f"文件状态为 '{record.status}'，只有 failed 或 ready 状态的文件可以重新索引",
        )

    # Find the file on disk
    file_path = None
    for fname in os.listdir(file_manager.storage_dir):
        if record.original_filename.split('.')[0] in fname and os.path.isfile(
            os.path.join(file_manager.storage_dir, fname)
        ):
            file_path = os.path.join(file_manager.storage_dir, fname)
            break

    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="原始文件已从磁盘删除，请重新上传",
        )

    # Mark as processing and enqueue
    record.status = "processing"
    record.error_message = None
    db.commit()
    db.refresh(record)

    background_tasks.add_task(importer.process_file, record.id, file_path)

    return {
        "id": record.id,
        "status": "processing",
        "message": "已加入处理队列",
    }


# ── View / Download images (rendered by ImageParser) ──────

@router.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve a page image rendered from an image-heavy PDF.

    Images are stored in data/images/ by ImageParser.
    Returns PNG with caching headers.
    """
    from ..services.image_parser import ImageParser

    img_parser = ImageParser()
    img_path = os.path.join(img_parser.image_dir, filename)

    if not os.path.isfile(img_path):
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(
        img_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ── Helpers ────────────────────────────────────────────────

def _serialize_file(record: KnowledgeFile) -> dict:
    """Convert a KnowledgeFile ORM object to a dict for JSON responses."""
    return {
        "id": record.id,
        "original_filename": record.original_filename,
        "file_type": record.file_type,
        "file_size": record.file_size,
        "category": getattr(record, "category", "") or "",
        "parse_mode": record.parse_mode,
        "chunk_count": record.chunk_count or 0,
        "status": record.status,
        "progress": record.progress or 0,
        "progress_step": record.progress_step or "",
        "error_message": record.error_message,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }
