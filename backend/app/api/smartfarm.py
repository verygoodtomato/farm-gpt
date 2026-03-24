from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.models.schemas import SmartFarmData
from app.services.llm.chat_service import chat_service
from app.services.smartfarm.optimizer import SmartFarmOptimizer
from app.services.smartfarm.simulator import CROP_PRESETS

router = APIRouter()

SMARTFARM_PROMPT = """당신은 스마트팜 환경제어 전문가입니다.
주어진 환경 데이터를 분석하여 최적의 환경 제어 방안을 추천해주세요.
JSON 형식 없이 자연어로 명확하게 답변하세요.
"""


@router.post("/analyze")
async def analyze_environment(data: SmartFarmData):
    """스마트팜 환경 데이터 분석 및 추천"""
    env_info = []
    if data.temperature is not None:
        env_info.append(f"온도: {data.temperature}°C")
    if data.humidity is not None:
        env_info.append(f"습도: {data.humidity}%")
    if data.co2 is not None:
        env_info.append(f"CO2: {data.co2}ppm")
    if data.light_intensity is not None:
        env_info.append(f"광량: {data.light_intensity}lux")
    if data.soil_moisture is not None:
        env_info.append(f"토양수분: {data.soil_moisture}%")

    messages = [
        {
            "role": "user",
            "content": f"현재 스마트팜 환경 데이터:\n{chr(10).join(env_info)}\n\n최적 환경으로 조정하기 위한 방안을 알려주세요.",
        }
    ]
    result = await chat_service.chat(messages, system=SMARTFARM_PROMPT)
    return {"analysis": result, "data": data.model_dump(exclude_none=True)}


@router.post("/simulate")
async def run_simulation(
    crop: str = Query("딸기", description="작물명"),
    hours: int = Query(24, ge=1, le=168, description="시뮬레이션 시간"),
    month: int = Query(1, ge=1, le=12, description="월"),
):
    """스마트팜 환경 시뮬레이션 실행"""
    if crop not in CROP_PRESETS:
        return {
            "status": "error",
            "message": f"지원하지 않는 작물: {crop}",
            "available": list(CROP_PRESETS.keys()),
        }

    optimizer = SmartFarmOptimizer(crop)
    result = optimizer.run_simulation(hours=hours, month=month)
    return result


@router.post("/compare")
async def compare_strategies(
    crop: str = Query("딸기"),
    month: int = Query(1, ge=1, le=12),
):
    """기본 제어 vs AI 최적화 제어 비교"""
    if crop not in CROP_PRESETS:
        return {"status": "error", "available": list(CROP_PRESETS.keys())}

    optimizer = SmartFarmOptimizer(crop)
    result = optimizer.compare_strategies(month=month)
    return result


@router.get("/optimal-ranges")
async def get_optimal_ranges():
    """주요 작물별 최적 환경 범위"""
    ranges = {}
    for name, config in CROP_PRESETS.items():
        ranges[name] = {
            "temperature": {
                "day": {"optimal": config.optimal_temp_day, "min": config.optimal_temp_day - 3, "max": config.optimal_temp_day + 3},
                "night": {"optimal": config.optimal_temp_night, "min": config.optimal_temp_night - 3, "max": config.optimal_temp_night + 3},
            },
            "humidity": {"optimal": config.optimal_humidity, "min": config.optimal_humidity - 10, "max": config.optimal_humidity + 10},
            "co2": {"optimal": config.optimal_co2, "min": 400, "max": 1200},
            "dli_target": config.optimal_dli,
        }
    return {"crops": ranges}


@router.get("/crops")
async def get_available_crops():
    """시뮬레이션 지원 작물 목록"""
    return {
        "crops": [
            {"name": name, "optimal_temp_day": c.optimal_temp_day, "optimal_temp_night": c.optimal_temp_night}
            for name, c in CROP_PRESETS.items()
        ]
    }
