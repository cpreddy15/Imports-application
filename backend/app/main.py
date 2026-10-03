import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from .config import settings
from .db import engine, init_db
from .routers import dashboard, shipments, tools
from .seed import seed

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.seed_demo_data:
        with Session(engine) as session:
            seed(session)
    yield


app = FastAPI(title="TradeFlow AI", version="1.0.0",
              description="AI-powered import-export management platform", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
app.include_router(dashboard.router)
app.include_router(shipments.router)
app.include_router(tools.router)

# Serve the built frontend (single-container deploy).
STATIC = Path(__file__).resolve().parent.parent / "static"
if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        target = STATIC / path
        return FileResponse(target if path and target.is_file() else STATIC / "index.html")
