from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import logging
from sqlalchemy import text
from app.database import engine

from app.config import get_settings
from app.routers import auth, products, stores, commerce, ai, operations, websocket, analytics

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("aurora")
if settings.environment.lower() in {"production", "prod"}:
    weak_secrets = {
        "change-me-in-production",
        "change-this-to-a-long-random-secret",
        "replace-with-at-least-32-random-characters",
    }
    if settings.jwt_secret in weak_secrets or len(settings.jwt_secret) < 32:
        raise RuntimeError("A strong JWT_SECRET is required in production")
    allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    if "*" in allowed_origins or any(origin.startswith("http://") for origin in allowed_origins):
        raise RuntimeError("Production CORS_ORIGINS must be explicit HTTPS origins")
app = FastAPI(title="AURORA X API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(stores.router)
app.include_router(commerce.router)
app.include_router(ai.router)
app.include_router(operations.router)
app.include_router(websocket.router)
app.include_router(analytics.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/ready")
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
