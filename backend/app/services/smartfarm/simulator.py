"""스마트팜 환경 시뮬레이터 - 온실 내부 환경 물리 모델"""

import math
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OutdoorCondition:
    """외부 기상 조건"""
    temperature: float = 5.0       # °C
    humidity: float = 60.0         # %
    solar_radiation: float = 0.0   # W/m²
    wind_speed: float = 2.0        # m/s
    co2: float = 420.0             # ppm


@dataclass
class GreenhouseState:
    """온실 내부 상태"""
    temperature: float = 20.0      # °C
    humidity: float = 65.0         # %
    co2: float = 600.0             # ppm
    light_intensity: float = 5000  # lux
    soil_moisture: float = 60.0    # %
    vpd: float = 0.0               # kPa (포차)

    # 누적 데이터
    energy_used_kwh: float = 0.0
    water_used_l: float = 0.0
    co2_injected_kg: float = 0.0
    dli: float = 0.0               # 일적산광량 (mol/m²/day)


@dataclass
class ControlAction:
    """환경 제어 명령"""
    heating: float = 0.0           # 0-100% (난방 출력)
    cooling: float = 0.0           # 0-100% (냉방/환기)
    ventilation: float = 0.0       # 0-100% (천창 개도)
    co2_injection: float = 0.0     # 0-100% (CO2 공급)
    irrigation: float = 0.0        # 0-100% (관수)
    lighting: float = 0.0          # 0-100% (보광등)
    curtain: float = 0.0           # 0-100% (보온커튼 폐쇄율)
    shading: float = 0.0           # 0-100% (차광막)


@dataclass
class CropConfig:
    """작물 설정"""
    name: str = "딸기"
    optimal_temp_day: float = 22.0
    optimal_temp_night: float = 8.0
    optimal_humidity: float = 65.0
    optimal_co2: float = 800.0
    optimal_dli: float = 14.0      # mol/m²/day
    transpiration_rate: float = 0.3  # 증산 계수
    photosynthesis_rate: float = 0.5  # 광합성 CO2 흡수율


CROP_PRESETS = {
    "딸기": CropConfig("딸기", 22, 8, 65, 800, 14, 0.3, 0.5),
    "토마토": CropConfig("토마토", 25, 15, 65, 900, 22, 0.4, 0.6),
    "파프리카": CropConfig("파프리카", 25, 17, 70, 800, 18, 0.35, 0.55),
}


class GreenhouseSimulator:
    """온실 환경 시뮬레이터

    물리 기반 모델로 온실 내부 환경을 시뮬레이션합니다.
    1 스텝 = 5분 (288 스텝 = 24시간)
    """

    STEP_MINUTES = 5
    STEPS_PER_HOUR = 12
    STEPS_PER_DAY = 288

    # 온실 물리 파라미터
    GREENHOUSE_AREA = 1000.0        # m²
    GREENHOUSE_VOLUME = 4000.0      # m³
    WALL_U_VALUE = 3.5              # W/m²·K (열관류율)
    WALL_AREA = 800.0               # m² (외피 면적)
    HEATING_CAPACITY = 200.0        # kW (난방 용량)
    COOLING_CAPACITY = 100.0        # kW (냉방 용량)
    VENTILATION_RATE = 50.0         # m³/s (최대 환기량)
    CO2_INJECTION_RATE = 0.5        # kg/min (CO2 공급 속도)
    IRRIGATION_RATE = 10.0          # L/min (관수 속도)
    LIGHT_POWER = 50.0              # kW (보광등 전력)
    LIGHT_OUTPUT = 30000.0          # lux (보광등 최대 출력)

    def __init__(self, crop: str = "딸기"):
        self.crop = CROP_PRESETS.get(crop, CROP_PRESETS["딸기"])
        self.state = GreenhouseState()
        self.outdoor = OutdoorCondition()
        self.current_step = 0
        self.history: list[dict] = []

    def reset(self, month: int = 1, hour: int = 6) -> GreenhouseState:
        """시뮬레이터 초기화"""
        self.state = GreenhouseState()
        self.current_step = hour * self.STEPS_PER_HOUR
        self.history = []
        self._update_outdoor(month)
        return self.state

    def _update_outdoor(self, month: int = 1):
        """외부 기상 업데이트 (시간대별 변화)"""
        hour = (self.current_step // self.STEPS_PER_HOUR) % 24

        # 월별 기본 온도 (한국 평균)
        monthly_base_temp = {
            1: -2, 2: 0, 3: 6, 4: 12, 5: 18, 6: 23,
            7: 26, 8: 27, 9: 22, 10: 15, 11: 7, 12: 0,
        }
        base = monthly_base_temp.get(month, 10)

        # 일교차 (사인 함수)
        diurnal = 5 * math.sin((hour - 6) * math.pi / 12) if 6 <= hour <= 18 else -3
        self.outdoor.temperature = base + diurnal + random.gauss(0, 0.5)

        # 일사량 (일출-일몰)
        if 6 <= hour <= 18:
            solar_angle = math.sin((hour - 6) * math.pi / 12)
            max_solar = 400 + 200 * math.sin((month - 1) * math.pi / 11)  # 여름 높음
            self.outdoor.solar_radiation = max(0, max_solar * solar_angle)
        else:
            self.outdoor.solar_radiation = 0

        # 습도 (야간 높음)
        self.outdoor.humidity = 65 + 15 * (1 - self.outdoor.solar_radiation / 600)
        self.outdoor.humidity = min(95, max(30, self.outdoor.humidity + random.gauss(0, 3)))

        self.outdoor.wind_speed = max(0.5, 2 + random.gauss(0, 1))

    def step(self, action: ControlAction, month: int = 1) -> tuple[GreenhouseState, dict]:
        """1 스텝(5분) 시뮬레이션 실행"""
        self._update_outdoor(month)
        dt = self.STEP_MINUTES * 60  # seconds

        # --- 온도 계산 ---
        # 열손실 (외피 통과)
        heat_loss = self.WALL_U_VALUE * self.WALL_AREA * (
            self.state.temperature - self.outdoor.temperature
        ) / 1000  # kW

        # 환기 열교환
        vent_rate = self.VENTILATION_RATE * (action.ventilation / 100)
        heat_ventilation = 1.2 * 1.005 * vent_rate * (
            self.state.temperature - self.outdoor.temperature
        ) / 1000  # kW

        # 보온커튼 효과 (열손실 감소)
        curtain_factor = 1 - 0.5 * (action.curtain / 100)
        total_heat_loss = (heat_loss * curtain_factor + heat_ventilation)

        # 난방/냉방
        heating_power = self.HEATING_CAPACITY * (action.heating / 100)
        cooling_power = self.COOLING_CAPACITY * (action.cooling / 100)

        # 일사 가열
        solar_heating = self.outdoor.solar_radiation * self.GREENHOUSE_AREA * 0.6 / 1000  # kW
        if action.shading > 0:
            solar_heating *= (1 - 0.7 * action.shading / 100)

        # 온도 변화
        net_heat = solar_heating + heating_power - cooling_power - total_heat_loss
        # Q = m * c * dT → dT = Q * dt / (m * c)
        air_mass = self.GREENHOUSE_VOLUME * 1.2  # kg
        temp_change = (net_heat * dt) / (air_mass * 1.005)
        self.state.temperature += temp_change
        self.state.temperature = max(-5, min(45, self.state.temperature))

        # --- 습도 계산 ---
        # 증산 (작물)
        transpiration = self.crop.transpiration_rate * max(0, self.state.temperature - 10) / 20
        # 환기 교환
        vent_humidity_change = vent_rate * (self.outdoor.humidity - self.state.humidity) * 0.001
        # 난방 제습 효과
        heating_dehumid = -heating_power * 0.02

        humidity_change = transpiration + vent_humidity_change + heating_dehumid
        self.state.humidity += humidity_change * (self.STEP_MINUTES / 60)
        self.state.humidity = max(30, min(98, self.state.humidity))

        # --- CO2 계산 ---
        # CO2 주입
        co2_injected = self.CO2_INJECTION_RATE * (action.co2_injection / 100) * self.STEP_MINUTES
        self.state.co2_injected_kg += co2_injected
        co2_ppm_added = co2_injected * 1000 * 1000 / (self.GREENHOUSE_VOLUME * 1.8)  # 대략적 변환

        # 광합성 CO2 흡수
        if self.state.light_intensity > 1000:
            photosynthesis = self.crop.photosynthesis_rate * (self.state.light_intensity / 30000) * 2
        else:
            photosynthesis = 0

        # 환기 CO2 교환
        vent_co2 = vent_rate * (self.outdoor.co2 - self.state.co2) * 0.0005

        self.state.co2 += co2_ppm_added - photosynthesis + vent_co2
        self.state.co2 = max(200, min(2000, self.state.co2))

        # --- 광량 계산 ---
        natural_light = self.outdoor.solar_radiation * 120 * (1 - 0.7 * action.shading / 100)
        artificial_light = self.LIGHT_OUTPUT * (action.lighting / 100)
        self.state.light_intensity = natural_light + artificial_light

        # DLI 누적
        ppfd = self.state.light_intensity * 0.02  # 대략적 lux → μmol/m²/s
        self.state.dli += ppfd * self.STEP_MINUTES * 60 / 1_000_000

        # --- 토양수분 ---
        irrigation_amount = self.IRRIGATION_RATE * (action.irrigation / 100) * self.STEP_MINUTES
        self.state.water_used_l += irrigation_amount
        evaporation = 0.1 * max(0, self.state.temperature - 10) / 20 * (self.STEP_MINUTES / 60)
        moisture_change = irrigation_amount * 0.01 - evaporation
        self.state.soil_moisture += moisture_change
        self.state.soil_moisture = max(10, min(95, self.state.soil_moisture))

        # --- VPD 계산 ---
        svp = 0.6108 * math.exp(17.27 * self.state.temperature / (self.state.temperature + 237.3))
        avp = svp * self.state.humidity / 100
        self.state.vpd = round(svp - avp, 3)

        # --- 에너지 소비 ---
        energy_step = (
            heating_power + cooling_power + self.LIGHT_POWER * (action.lighting / 100)
        ) * (self.STEP_MINUTES / 60)  # kWh
        self.state.energy_used_kwh += energy_step

        # 스텝 증가
        self.current_step += 1
        hour = (self.current_step // self.STEPS_PER_HOUR) % 24

        # 기록
        record = {
            "step": self.current_step,
            "hour": hour,
            "minute": (self.current_step % self.STEPS_PER_HOUR) * self.STEP_MINUTES,
            "indoor": {
                "temperature": round(self.state.temperature, 1),
                "humidity": round(self.state.humidity, 1),
                "co2": round(self.state.co2),
                "light": round(self.state.light_intensity),
                "soil_moisture": round(self.state.soil_moisture, 1),
                "vpd": self.state.vpd,
            },
            "outdoor": {
                "temperature": round(self.outdoor.temperature, 1),
                "humidity": round(self.outdoor.humidity, 1),
                "solar": round(self.outdoor.solar_radiation),
            },
            "action": {
                "heating": action.heating,
                "cooling": action.cooling,
                "ventilation": action.ventilation,
                "co2_injection": action.co2_injection,
                "lighting": action.lighting,
                "curtain": action.curtain,
            },
            "energy_kwh": round(energy_step, 3),
            "cumulative_energy_kwh": round(self.state.energy_used_kwh, 2),
        }
        self.history.append(record)

        info = {
            "energy_step_kwh": energy_step,
            "dli": round(self.state.dli, 2),
            "vpd": self.state.vpd,
        }

        return self.state, info

    def get_score(self) -> dict:
        """현재 환경 상태의 적합도 점수 (0-100)"""
        hour = (self.current_step // self.STEPS_PER_HOUR) % 24
        is_day = 6 <= hour <= 18

        optimal_temp = self.crop.optimal_temp_day if is_day else self.crop.optimal_temp_night
        temp_score = max(0, 100 - abs(self.state.temperature - optimal_temp) * 8)
        humidity_score = max(0, 100 - abs(self.state.humidity - self.crop.optimal_humidity) * 3)
        co2_score = max(0, 100 - abs(self.state.co2 - self.crop.optimal_co2) * 0.1) if is_day else 80
        vpd_score = max(0, 100 - abs(self.state.vpd - 0.8) * 100) if is_day else 80

        overall = (temp_score * 0.35 + humidity_score * 0.25 + co2_score * 0.25 + vpd_score * 0.15)

        return {
            "overall": round(overall, 1),
            "temperature": round(temp_score, 1),
            "humidity": round(humidity_score, 1),
            "co2": round(co2_score, 1),
            "vpd": round(vpd_score, 1),
            "is_day": is_day,
        }
