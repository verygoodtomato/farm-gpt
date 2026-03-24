"""API 엔드포인트 테스트"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_chat_health(self):
        response = client.get("/api/chat/health")
        assert response.status_code == 200


class TestSmartFarmAPI:
    def test_optimal_ranges(self):
        response = client.get("/api/smartfarm/optimal-ranges")
        assert response.status_code == 200
        data = response.json()
        assert "crops" in data
        assert "딸기" in data["crops"]

    def test_available_crops(self):
        response = client.get("/api/smartfarm/crops")
        assert response.status_code == 200
        crops = response.json()["crops"]
        assert len(crops) >= 3

    def test_simulate(self):
        response = client.post("/api/smartfarm/simulate?crop=딸기&hours=2&month=1")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["summary"]["avg_score"] > 0

    def test_simulate_invalid_crop(self):
        response = client.post("/api/smartfarm/simulate?crop=두리안&hours=2&month=1")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "error"

    def test_compare_strategies(self):
        response = client.post("/api/smartfarm/compare?crop=딸기&month=1")
        assert response.status_code == 200
        data = response.json()
        assert "optimized" in data
        assert "basic" in data


class TestAnalyticsAPI:
    def test_price_history(self):
        response = client.get("/api/analytics/price-history/딸기")
        assert response.status_code == 200
        data = response.json()
        assert "monthly_prices" in data
        assert len(data["monthly_prices"]) == 12

    def test_predict_yield(self):
        response = client.post(
            "/api/analytics/predict-yield?crop_type=딸기&area_m2=1000&avg_temp_day=22"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_predicted_yield_kg"] > 0

    def test_available_crops(self):
        response = client.get("/api/analytics/available-crops")
        assert response.status_code == 200


class TestDiagnosisAPI:
    def test_supported_crops(self):
        response = client.get("/api/diagnosis/crops")
        assert response.status_code == 200
        data = response.json()
        assert "딸기" in data
        assert "토마토" in data
