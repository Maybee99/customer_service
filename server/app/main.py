from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .utils.logger import logger
from .api import chat, conversations, knowledge, chat_stream

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(knowledge.router, prefix="/api", tags=["Knowledge"])
app.include_router(chat_stream.router, prefix="/api", tags=["Chat"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    logger.info(f"Milvus: {settings.milvus_uri}")
    logger.info(f"Database: {settings.database_url}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
