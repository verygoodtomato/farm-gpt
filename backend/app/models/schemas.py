from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = True
    use_rag: bool = True  # RAG 지식베이스 활용 여부


class ChatResponse(BaseModel):
    content: str
    created_at: datetime = None

    def __init__(self, **data):
        if data.get("created_at") is None:
            data["created_at"] = datetime.now()
        super().__init__(**data)


class DiagnosisRequest(BaseModel):
    crop_type: Optional[str] = None
    description: Optional[str] = None


class DiagnosisResponse(BaseModel):
    disease_name: str
    confidence: float
    description: str
    treatment: str


class SmartFarmData(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None
    light_intensity: Optional[float] = None
    soil_moisture: Optional[float] = None


class SmartFarmRecommendation(BaseModel):
    parameter: str
    current_value: float
    recommended_value: float
    action: str


class PredictionRequest(BaseModel):
    crop_type: str
    region: Optional[str] = None
    period: Optional[str] = "monthly"


class PredictionResponse(BaseModel):
    crop_type: str
    predictions: list[dict]
    confidence_interval: Optional[dict] = None
