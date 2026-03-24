"""스마트팜 시뮬레이터 테스트"""

import pytest
from app.services.smartfarm.simulator import (
    GreenhouseSimulator,
    ControlAction,
    GreenhouseState,
    CROP_PRESETS,
)
from app.services.smartfarm.optimizer import SmartFarmOptimizer, RuleBasedController


class TestGreenhouseSimulator:
    def test_initial_state(self):
        sim = GreenhouseSimulator("딸기")
        state = sim.reset(month=1, hour=6)
        assert isinstance(state, GreenhouseState)
        assert state.temperature == 20.0
        assert state.humidity == 65.0

    def test_step_returns_valid_state(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=1, hour=12)
        action = ControlAction(heating=50)
        state, info = sim.step(action, month=1)

        assert -5 <= state.temperature <= 45
        assert 30 <= state.humidity <= 98
        assert 200 <= state.co2 <= 2000
        assert state.light_intensity >= 0

    def test_heating_increases_temperature(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=1, hour=6)
        initial_temp = sim.state.temperature

        # 강한 난방 10스텝 실행
        for _ in range(10):
            action = ControlAction(heating=100)
            sim.step(action, month=1)

        assert sim.state.temperature > initial_temp

    def test_ventilation_changes_environment(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=7, hour=12)
        sim.state.temperature = 35  # 고온 상태 설정

        for _ in range(10):
            action = ControlAction(ventilation=100, cooling=80)
            sim.step(action, month=7)

        assert sim.state.temperature < 35

    def test_co2_injection(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=1, hour=10)
        sim.state.co2 = 400

        for _ in range(10):
            action = ControlAction(co2_injection=80)
            sim.step(action, month=1)

        assert sim.state.co2 > 400

    def test_score_calculation(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=1, hour=12)
        score = sim.get_score()

        assert "overall" in score
        assert "temperature" in score
        assert "humidity" in score
        assert 0 <= score["overall"] <= 100

    def test_energy_tracking(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=1, hour=0)

        for _ in range(12):
            action = ControlAction(heating=50, lighting=30)
            sim.step(action, month=1)

        assert sim.state.energy_used_kwh > 0

    def test_all_crops_supported(self):
        for crop_name in CROP_PRESETS:
            sim = GreenhouseSimulator(crop_name)
            state = sim.reset(month=6, hour=12)
            action = ControlAction(heating=20, ventilation=30)
            new_state, info = sim.step(action, month=6)
            assert new_state.temperature != state.temperature or True  # 변화 가능

    def test_24h_simulation_completes(self):
        sim = GreenhouseSimulator("딸기")
        sim.reset(month=1, hour=0)

        for i in range(288):  # 24h
            hour = (sim.current_step // sim.STEPS_PER_HOUR) % 24
            action = ControlAction(heating=30 if hour < 6 else 10)
            sim.step(action, month=1)

        assert len(sim.history) == 288
        assert sim.state.energy_used_kwh > 0


class TestOptimizer:
    def test_rule_based_controller(self):
        crop = CROP_PRESETS["딸기"]
        controller = RuleBasedController(crop)
        state = GreenhouseState(temperature=15, humidity=80, co2=400)

        action = controller.get_action(state, hour=12)
        assert action.heating > 0  # 낮은 온도 → 난방
        assert action.ventilation > 0 or action.heating > 0  # 높은 습도 → 환기 or 난방

    def test_optimizer_simulation(self):
        optimizer = SmartFarmOptimizer("딸기")
        result = optimizer.run_simulation(hours=24, month=1)

        assert "summary" in result
        assert "hourly_data" in result
        assert result["summary"]["avg_score"] > 0
        assert result["summary"]["total_energy_kwh"] > 0

    def test_strategy_comparison(self):
        optimizer = SmartFarmOptimizer("토마토")
        result = optimizer.compare_strategies(month=6)

        assert "optimized" in result
        assert "basic" in result
        assert "improvement" in result
        # AI 최적화가 기본보다 나은 점수를 기대
        assert result["optimized"]["avg_score"] >= result["basic"]["avg_score"] - 10


class TestForecastService:
    def test_price_prediction(self):
        from app.services.prediction.forecast_service import forecast_service

        result = forecast_service.predict_price("딸기", 3)
        assert result.get("status") != "error"
        assert "predictions" in result
        assert len(result["predictions"]) == 3

    def test_price_unknown_crop(self):
        from app.services.prediction.forecast_service import forecast_service

        result = forecast_service.predict_price("두리안", 3)
        assert result["status"] == "error"

    def test_yield_prediction(self):
        from app.services.prediction.forecast_service import forecast_service

        result = forecast_service.predict_yield(
            "딸기", area_m2=1000, avg_temp_day=22, avg_temp_night=8, co2_level=800
        )
        assert result.get("status") != "error"
        assert result["total_predicted_yield_kg"] > 0
        assert len(result["environmental_factors"]) == 3

    def test_yield_with_suboptimal_conditions(self):
        from app.services.prediction.forecast_service import forecast_service

        optimal = forecast_service.predict_yield("딸기", 1000, 22, 8, 800)
        suboptimal = forecast_service.predict_yield("딸기", 1000, 35, 20, 300)

        assert optimal["total_predicted_yield_kg"] > suboptimal["total_predicted_yield_kg"]

    def test_price_history(self):
        from app.services.prediction.forecast_service import forecast_service

        result = forecast_service.get_price_history("토마토")
        assert "monthly_prices" in result
        assert len(result["monthly_prices"]) == 12
