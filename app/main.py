from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title="MIRANTES API",
    version="1.0.0",
    description="Backend hospedado no Render com PostgreSQL do Supabase.",
)

origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=bool(origins),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"service": "MIRANTES API", "status": "online"}
