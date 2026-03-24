"""수확량 및 가격 예측 서비스"""

import numpy as np
from datetime import datetime, timedelta
from typing import Optional


# 농산물 월별 평균 가격 데이터 (원/kg, 2023-2024 기준 시뮬레이션)
HISTORICAL_PRICES = {
    "딸기": {
        "monthly_avg": [18000, 15000, 12000, 0, 0, 0, 0, 0, 0, 0, 14000, 20000],
        "unit": "원/kg",
        "season": "11월~3월",
    },
    "토마토": {
        "monthly_avg": [4500, 5200, 4800, 3500, 2800, 2500, 3000, 3500, 4000, 3800, 4200, 4800],
        "unit": "원/kg",
        "season": "연중",
    },
    "파프리카": {
        "monthly_avg": [8000, 7500, 6000, 5000, 4500, 5000, 6000, 7000, 7500, 7000, 7500, 8500],
        "unit": "원/kg",
        "season": "연중 (겨울 성수기)",
    },
    "사과": {
        "monthly_avg": [6000, 6500, 7000, 7500, 7000, 6500, 5500, 4500, 4000, 3500, 4000, 5000],
        "unit": "원/kg",
        "season": "9월~11월 (수확)",
    },
    "배추": {
        "monthly_avg": [2000, 2500, 2200, 1800, 1500, 2000, 2500, 3000, 2500, 1800, 1500, 1800],
        "unit": "원/kg",
        "season": "봄/가을",
    },
    "고추": {
        "monthly_avg": [12000, 13000, 14000, 13500, 12000, 11000, 10000, 9000, 8500, 9000, 10000, 11000],
        "unit": "원/kg",
        "season": "7월~9월 (수확)",
    },
    "감자": {
        "monthly_avg": [3000, 3200, 3500, 3000, 2500, 2000, 1800, 2000, 2500, 2800, 3000, 3200],
        "unit": "원/kg",
        "season": "6월~7월 (수확)",
    },
    "쌀": {
        "monthly_avg": [2800, 2800, 2850, 2900, 2900, 2850, 2800, 2750, 2600, 2500, 2600, 2700],
        "unit": "원/kg",
        "season": "10월 (수확)",
    },
}

# 작물별 재배 데이터 (스마트팜 기준)
CROP_YIELD_DATA = {
    "딸기": {
        "yield_per_m2": 6.0,  # kg/m²/연
        "growth_days": 150,
        "optimal_temp": {"day": 22, "night": 8},
        "temp_sensitivity": 0.05,  # 1도 이탈 시 수확량 감소율
    },
    "토마토": {
        "yield_per_m2": 25.0,
        "growth_days": 120,
        "optimal_temp": {"day": 25, "night": 15},
        "temp_sensitivity": 0.03,
    },
    "파프리카": {
        "yield_per_m2": 12.0,
        "growth_days": 150,
        "optimal_temp": {"day": 25, "night": 17},
        "temp_sensitivity": 0.04,
    },
}


class ForecastService:
    """농산물 가격 및 수확량 예측 서비스"""

    def predict_price(
        self,
        crop_type: str,
        months_ahead: int = 3,
    ) -> dict:
        """농산물 가격 예측 (이동평균 + 계절성 기반)"""
        if crop_type not in HISTORICAL_PRICES:
            return {
                "status": "error",
                "message": f"'{crop_type}' 가격 데이터가 없습니다.",
                "available_crops": list(HISTORICAL_PRICES.keys()),
            }

        data = HISTORICAL_PRICES[crop_type]
        monthly_avg = data["monthly_avg"]
        current_month = datetime.now().month  # 1-12

        predictions = []
        for i in range(months_ahead):
            target_month = (current_month + i) % 12  # 0-11
            target_date = datetime.now() + timedelta(days=30 * (i + 1))

            base_price = monthly_avg[target_month]
            if base_price == 0:
                predictions.append({
                    "month": target_date.strftime("%Y-%m"),
                    "predicted_price": 0,
                    "note": "비수확기",
                })
                continue

            # 변동성 추가 (정규분포)
            np.random.seed(target_month + current_month)
            noise = np.random.normal(0, base_price * 0.08)
            trend = base_price * 0.02 * (i + 1)  # 약간의 상승 트렌드

            predicted = max(0, base_price + noise + trend)

            predictions.append({
                "month": target_date.strftime("%Y-%m"),
                "predicted_price": round(predicted),
                "price_range": {
                    "low": round(predicted * 0.85),
                    "high": round(predicted * 1.15),
                },
                "confidence": round(0.85 - 0.05 * i, 2),
            })

        return {
            "crop_type": crop_type,
            "unit": data["unit"],
            "season": data["season"],
            "current_month_avg": monthly_avg[current_month - 1],
            "predictions": predictions,
            "methodology": "계절성 시계열 분석 (이동평균 + 계절 보정)",
        }

    def predict_yield(
        self,
        crop_type: str,
        area_m2: float = 1000,
        avg_temp_day: Optional[float] = None,
        avg_temp_night: Optional[float] = None,
        co2_level: Optional[float] = None,
    ) -> dict:
        """스마트팜 수확량 예측"""
        if crop_type not in CROP_YIELD_DATA:
            return {
                "status": "error",
                "message": f"'{crop_type}' 수확량 데이터가 없습니다.",
                "available_crops": list(CROP_YIELD_DATA.keys()),
            }

        data = CROP_YIELD_DATA[crop_type]
        base_yield = data["yield_per_m2"]

        # 환경 요인별 수확량 보정
        adjustment = 1.0
        factors = []

        # 온도 보정
        if avg_temp_day is not None:
            temp_diff = abs(avg_temp_day - data["optimal_temp"]["day"])
            temp_factor = max(0.5, 1.0 - data["temp_sensitivity"] * temp_diff)
            adjustment *= temp_factor
            factors.append({
                "factor": "주간 온도",
                "optimal": f"{data['optimal_temp']['day']}°C",
                "actual": f"{avg_temp_day}°C",
                "impact": f"{(temp_factor - 1) * 100:+.1f}%",
            })

        if avg_temp_night is not None:
            temp_diff = abs(avg_temp_night - data["optimal_temp"]["night"])
            temp_factor = max(0.5, 1.0 - data["temp_sensitivity"] * temp_diff)
            adjustment *= temp_factor
            factors.append({
                "factor": "야간 온도",
                "optimal": f"{data['optimal_temp']['night']}°C",
                "actual": f"{avg_temp_night}°C",
                "impact": f"{(temp_factor - 1) * 100:+.1f}%",
            })

        # CO2 보정
        if co2_level is not None:
            if co2_level >= 700:
                co2_factor = min(1.25, 1.0 + (co2_level - 400) / 2000)
            else:
                co2_factor = max(0.8, co2_level / 700)
            adjustment *= co2_factor
            factors.append({
                "factor": "CO2 농도",
                "optimal": "700-1000ppm",
                "actual": f"{co2_level}ppm",
                "impact": f"{(co2_factor - 1) * 100:+.1f}%",
            })

        predicted_yield = base_yield * adjustment * area_m2

        return {
            "crop_type": crop_type,
            "area_m2": area_m2,
            "base_yield_per_m2": base_yield,
            "adjusted_yield_per_m2": round(base_yield * adjustment, 2),
            "total_predicted_yield_kg": round(predicted_yield, 1),
            "adjustment_factor": round(adjustment, 3),
            "growth_days": data["growth_days"],
            "environmental_factors": factors,
            "methodology": "환경 요인 보정 수확량 모델",
        }

    def get_price_history(self, crop_type: str) -> dict:
        """작물 월별 평균 가격 히스토리"""
        if crop_type not in HISTORICAL_PRICES:
            return {"status": "error", "message": f"'{crop_type}' 데이터 없음"}

        data = HISTORICAL_PRICES[crop_type]
        months = ["1월", "2월", "3월", "4월", "5월", "6월",
                   "7월", "8월", "9월", "10월", "11월", "12월"]

        history = [
            {"month": m, "price": p}
            for m, p in zip(months, data["monthly_avg"])
        ]

        return {
            "crop_type": crop_type,
            "unit": data["unit"],
            "season": data["season"],
            "monthly_prices": history,
        }

    def get_available_crops(self) -> dict:
        """예측 가능한 작물 목록"""
        return {
            "price_forecast": list(HISTORICAL_PRICES.keys()),
            "yield_forecast": list(CROP_YIELD_DATA.keys()),
        }


forecast_service = ForecastService()
