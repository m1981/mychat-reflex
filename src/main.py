# File: src/main.py
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.features.chat.presentation.routes import router as chat_router
from src.core.database.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set specific loggers to DEBUG for detailed tracing
logging.getLogger("src.infrastructure.llm.anthropic_adapter").setLevel(logging.DEBUG)
logging.getLogger("src.features.chat.use_cases.send_message").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


# Lifespan event to create DB tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting FastAPI application")
    logger.info("📊 Initializing database...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("🛑 Shutting down FastAPI application")


app = FastAPI(title="Super Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

logger.info("📡 Chat router registered at /chat")

if __name__ == "__main__":
    logger.info("🌐 Starting server on http://0.0.0.0:8080")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)
