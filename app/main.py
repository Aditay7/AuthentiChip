from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.auth_router import router as auth_router
from app.api.v1.ic import router as ic_router
from app.core.config import get_settings
from app.db.client import close_client, connect_client, get_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_client()
    try:
        yield
    finally:
        await close_client()


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(ic_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {"message": "Server is running"}


@app.get("/health")
async def health() -> dict:
    db = get_database()
    await db.command("ping")
    return {"status": "ok"}