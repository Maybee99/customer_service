 from fastapi import APIRouter
 router = APIRouter()
 @router.post("/knowledge/import")
 async def import_document():
     return {"status": "success"}
 @router.get("/knowledge/files")
 async def list_files():
     return {"files": []}
