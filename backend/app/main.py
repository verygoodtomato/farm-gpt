from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import chat, diagnosis, smartfarm, analytics, knowledge

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="농업 컨설팅 AI 플랫폼 - 스마트농업 AI 경진대회",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["Diagnosis"])
app.include_router(smartfarm.router, prefix="/api/smartfarm", tags=["SmartFarm"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
