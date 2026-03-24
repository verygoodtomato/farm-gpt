"""스마트팜 환경 제어 최적화 - 규칙 기반 + AI 하이브리드"""

from app.services.smartfarm.simulator import (
    GreenhouseSimulator,
    GreenhouseState,
    ControlAction,
    CropConfig,
    CROP_PRESETS,
)


class RuleBasedController:
    """규칙 기반 환경 제어기

    작물별 최적 환경 범위를 기준으로 PID 유사 제어를 수행합니다.
    """

    def __init__(self, crop: CropConfig):
        self.crop = crop
        self._prev_temp_error = 0.0

    def get_action(self, state: GreenhouseState, hour: int) -> ControlAction:
        """현재 상태에 기반한 제어 명령 생성"""
        is_day = 6 <= hour <= 18
        action = ControlAction()

        # === 온도 제어 ===
        target_temp = self.crop.optimal_temp_day if is_day else self.crop.optimal_temp_night
        temp_error = target_temp - state.temperature

        # P 제어 + 약간의 D 제어
        p_gain = 8.0
        d_gain = 2.0
        temp_signal = p_gain * temp_error + d_gain * (temp_error - self._prev_temp_error)
        self._prev_temp_error = temp_error

        if temp_signal > 0:
            action.heating = min(100, max(0, temp_signal * 5))
        elif temp_signal < 0:
            action.cooling = min(100, max(0, -temp_signal * 5))
            action.ventilation = min(80, max(0, -temp_signal * 3))

        # === 습도 제어 ===
        humidity_error = state.humidity - self.crop.optimal_humidity

        if humidity_error > 10:
            # 습도 높음 → 환기 + 난방
            action.ventilation = max(action.ventilation, min(60, humidity_error * 3))
            action.heating = max(action.heating, 10)
        elif humidity_error < -10:
            # 습도 낮음 → 환기 줄임
            action.ventilation = min(action.ventilation, 10)

        # === CO2 제어 ===
        if is_day and state.light_intensity > 2000:
            co2_error = self.crop.optimal_co2 - state.co2
            if co2_error > 50:
                action.co2_injection = min(80, max(0, co2_error * 0.3))
            # 환기 중이면 CO2 주입 감소
            if action.ventilation > 30:
                action.co2_injection *= 0.3

        # === 보광등 제어 ===
        if is_day and state.light_intensity < 8000:
            # 자연광 부족 시 보광
            light_deficit = 8000 - state.light_intensity
            action.lighting = min(80, max(0, light_deficit / 300))
        elif not is_day:
            action.lighting = 0

        # === 보온커튼 ===
        if not is_day:
            action.curtain = 90  # 야간 보온
        elif is_day and state.temperature < target_temp - 3:
            action.curtain = 50  # 주간 저온 시 부분 폐쇄
        else:
            action.curtain = 0

        # === 차광막 ===
        if is_day and state.temperature > target_temp + 3:
            action.shading = min(70, (state.temperature - target_temp - 3) * 15)
        else:
            action.shading = 0

        # === 관수 ===
        if state.soil_moisture < 40:
            action.irrigation = 60
        elif state.soil_moisture < 50:
            action.irrigation = 30
        elif state.soil_moisture > 75:
            action.irrigation = 0
        else:
            action.irrigation = 10

        return action


class SmartFarmOptimizer:
    """스마트팜 환경 최적화 시뮬레이션 실행기"""

    def __init__(self, crop: str = "딸기"):
        self.crop_name = crop
        self.crop_config = CROP_PRESETS.get(crop, CROP_PRESETS["딸기"])
        self.simulator = GreenhouseSimulator(crop)
        self.controller = RuleBasedController(self.crop_config)

    def run_simulation(
        self,
        hours: int = 24,
        month: int = 1,
        start_hour: int = 0,
    ) -> dict:
        """시뮬레이션 실행"""
        self.simulator.reset(month=month, hour=start_hour)
        steps = hours * self.simulator.STEPS_PER_HOUR

        scores = []
        hourly_data = []
        current_hour_data = {"scores": [], "energy": 0}
        last_hour = start_hour

        for i in range(steps):
            hour = (self.simulator.current_step // self.simulator.STEPS_PER_HOUR) % 24

            # 시간 변경 감지 → 시간별 집계
            if hour != last_hour:
                if current_hour_data["scores"]:
                    avg_score = sum(current_hour_data["scores"]) / len(current_hour_data["scores"])
                    hourly_data.append({
                        "hour": last_hour,
                        "avg_score": round(avg_score, 1),
                        "energy_kwh": round(current_hour_data["energy"], 3),
                    })
                current_hour_data = {"scores": [], "energy": 0}
                last_hour = hour

            action = self.controller.get_action(self.simulator.state, hour)
            state, info = self.simulator.step(action, month=month)
            score = self.simulator.get_score()
            scores.append(score["overall"])
            current_hour_data["scores"].append(score["overall"])
            current_hour_data["energy"] += info["energy_step_kwh"]

        # 마지막 시간 집계
        if current_hour_data["scores"]:
            avg_score = sum(current_hour_data["scores"]) / len(current_hour_data["scores"])
            hourly_data.append({
                "hour": last_hour,
                "avg_score": round(avg_score, 1),
                "energy_kwh": round(current_hour_data["energy"], 3),
            })

        avg_score = sum(scores) / len(scores) if scores else 0
        final_state = self.simulator.state
        final_score = self.simulator.get_score()

        return {
            "crop": self.crop_name,
            "duration_hours": hours,
            "month": month,
            "summary": {
                "avg_score": round(avg_score, 1),
                "final_score": final_score,
                "total_energy_kwh": round(final_state.energy_used_kwh, 2),
                "total_water_l": round(final_state.water_used_l, 1),
                "total_co2_kg": round(final_state.co2_injected_kg, 2),
                "dli": round(final_state.dli, 2),
            },
            "final_state": {
                "temperature": round(final_state.temperature, 1),
                "humidity": round(final_state.humidity, 1),
                "co2": round(final_state.co2),
                "light": round(final_state.light_intensity),
                "soil_moisture": round(final_state.soil_moisture, 1),
                "vpd": final_state.vpd,
            },
            "hourly_data": hourly_data,
            "history_sample": self.simulator.history[::12],  # 매 시간 1개 샘플
        }

    def compare_strategies(self, month: int = 1) -> dict:
        """제어 전략 비교 (기본 vs 최적화)"""

        # 최적화 제어
        optimized = self.run_simulation(hours=24, month=month)

        # 기본 제어 (고정 설정)
        basic_sim = GreenhouseSimulator(self.crop_name)
        basic_sim.reset(month=month, hour=0)

        basic_scores = []
        for i in range(self.simulator.STEPS_PER_DAY):
            hour = (basic_sim.current_step // basic_sim.STEPS_PER_HOUR) % 24
            # 단순 고정 제어
            action = ControlAction(
                heating=50 if hour < 6 or hour > 18 else 20,
                cooling=30 if 10 <= hour <= 16 else 0,
                ventilation=20,
                co2_injection=30 if 8 <= hour <= 16 else 0,
                lighting=0,
                curtain=80 if hour < 6 or hour > 18 else 0,
            )
            state, info = basic_sim.step(action, month=month)
            score = basic_sim.get_score()
            basic_scores.append(score["overall"])

        basic_avg = sum(basic_scores) / len(basic_scores)

        return {
            "crop": self.crop_name,
            "month": month,
            "optimized": {
                "avg_score": optimized["summary"]["avg_score"],
                "energy_kwh": optimized["summary"]["total_energy_kwh"],
                "water_l": optimized["summary"]["total_water_l"],
            },
            "basic": {
                "avg_score": round(basic_avg, 1),
                "energy_kwh": round(basic_sim.state.energy_used_kwh, 2),
                "water_l": round(basic_sim.state.water_used_l, 1),
            },
            "improvement": {
                "score_diff": round(optimized["summary"]["avg_score"] - basic_avg, 1),
                "energy_saving_pct": round(
                    (1 - optimized["summary"]["total_energy_kwh"] / max(basic_sim.state.energy_used_kwh, 0.01)) * 100, 1
                ),
            },
        }
