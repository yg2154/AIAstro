import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat as chat_router
from app.core.config import get_settings
from app.services.rag_engine import get_rag_engine
from app.services.session_manager import get_session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger.info("Starting MyNaksh — Vedic Astrology AI (env=%s)", settings.app_env)

    # Build FAISS index
    rag = get_rag_engine()
    try:
        rag.build_index()
        logger.info("RAG index ready (%d chunks)", rag._index.ntotal if rag._index else 0)
    except Exception as exc:
        logger.error("RAG index build failed: %s", exc)

    # Start session cleanup background task
    session_mgr = get_session_manager()
    session_mgr.start_cleanup()

    yield

    # Shutdown
    session_mgr.stop_cleanup()
    logger.info("MyNaksh shutdown complete.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MyNaksh — Vedic Astrology AI",
        description="Multi-turn conversational Vedic astrology with RAG and intent detection.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        rag = get_rag_engine()
        return {"status": "ok", "rag_ready": rag.is_ready}

    return app


app = create_app()
