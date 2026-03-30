from fastapi import APIRouter, Query
from typing import Optional

from app.models.schemas import PredictionRequest
from app.services.prediction.forecast_service import forecast_service
from app.services.llm.chat_service import chat_service

router = APIRouter()

ANALYTICS_PROMPT = """당신은 농업 데이터 분석 전문가입니다.
주어진 데이터를 기반으로 농산물 시장 동향, 수확량 예측, 재배 전략을 분석합니다.

분석 시 다음을 포함하세요:
- 데이터 기반 인사이트
- 과거 추세 기반 예측 해석
- 리스크 요인 및 기회
- 농업인을 위한 실행 가능한 제안
"""


@router.post("/predict-price")
async def predict_price(
    crop_type: str = Query(..., description="작물명"),
    months_ahead: int = Query(3, ge=1, le=12, description="예측 개월 수"),
):
    """농산물 가격 예측"""
    prediction = forecast_service.predict_price(crop_type, months_ahead)

    if prediction.get("status") == "error":
        return prediction

    # AI 분석 추가
    pred_summary = "\n".join(
        f"- {p['month']}: {p.get('predicted_price', '비수확기')}원"
        for p in prediction["predictions"]
    )

    messages = [
        {
            "role": "user",
            "content": (
                f"{crop_type}의 향후 {months_ahead}개월 가격 예측 결과입니다:\n"
                f"현재 월 평균: {prediction['current_month_avg']}원/kg\n"
                f"수확 시기: {prediction['season']}\n"
                f"예측:\n{pred_summary}\n\n"
                f"이 데이터를 바탕으로 시장 동향과 농가 전략을 분석해주세요."
            ),
        }
    ]
    ai_analysis = await chat_service.chat(messages, system=ANALYTICS_PROMPT, use_advanced=True)
    prediction["ai_analysis"] = ai_analysis

    return prediction


@router.post("/predict-yield")
async def predict_yield(
    crop_type: str = Query(...),
    area_m2: float = Query(1000, gt=0),
    avg_temp_day: Optional[float] = Query(None),
    avg_temp_night: Optional[float] = Query(None),
    co2_level: Optional[float] = Query(None),
):
    """스마트팜 수확량 예측"""
    prediction = forecast_service.predict_yield(
        crop_type=crop_type,
        area_m2=area_m2,
        avg_temp_day=avg_temp_day,
        avg_temp_night=avg_temp_night,
        co2_level=co2_level,
    )
    return prediction


@router.get("/price-history/{crop_type}")
async def get_price_history(crop_type: str):
    """작물 월별 평균 가격 히스토리"""
    return forecast_service.get_price_history(crop_type)


@router.get("/market-info/{crop_type}")
async def get_market_info(crop_type: str):
    """농산물 시장 정보 (AI 분석)"""
    # 가격 데이터 조회
    price_data = forecast_service.get_price_history(crop_type)
    price_prediction = forecast_service.predict_price(crop_type, 3)

    context = ""
    if price_data.get("monthly_prices"):
        prices = ", ".join(
            f"{p['month']}: {p['price']}원" for p in price_data["monthly_prices"] if p["price"] > 0
        )
        context = f"\n월별 평균 가격: {prices}\n수확 시기: {price_data.get('season', '')}"

    messages = [
        {
            "role": "user",
            "content": f"{crop_type}의 최근 시장 동향과 가격 전망을 알려주세요.{context}",
        }
    ]
    analysis = await chat_service.chat(messages, system=ANALYTICS_PROMPT)

    return {
        "crop_type": crop_type,
        "analysis": analysis,
        "price_data": price_data if "status" not in price_data else None,
        "price_forecast": price_prediction if "status" not in price_prediction else None,
    }


@router.get("/available-crops")
async def get_available_crops():
    """예측 가능한 작물 목록"""
    return forecast_service.get_available_crops()
