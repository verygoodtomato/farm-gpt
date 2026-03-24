"""농업 데이터 수집기 - 공공 API 연동"""

import httpx
from typing import Optional
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()


class WeatherCollector:
    """기상청 API 기반 날씨 데이터 수집"""

    BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""

    async def get_forecast(self, nx: int, ny: int) -> dict:
        """동네예보 조회 (격자 좌표 기반)"""
        if not self.api_key:
            return {"status": "error", "message": "기상청 API 키가 설정되지 않았습니다."}

        now = datetime.now()
        base_date = now.strftime("%Y%m%d")
        base_time = "0500"  # 가장 가까운 발표 시각

        params = {
            "serviceKey": self.api_key,
            "numOfRows": 100,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/getVilageFcst",
                params=params,
                timeout=10.0,
            )
            return response.json()


class KamisCollector:
    """KAMIS(농산물유통정보) API 기반 가격 데이터"""

    BASE_URL = "http://www.kamis.or.kr/service/price/xml.do"

    def __init__(self, api_key: Optional[str] = None, cert_id: Optional[str] = None):
        self.api_key = api_key or ""
        self.cert_id = cert_id or ""

    async def get_daily_price(
        self,
        product_code: str,
        region_code: str = "1101",
    ) -> dict:
        """일별 농산물 가격 조회"""
        if not self.api_key:
            return {"status": "error", "message": "KAMIS API 키가 설정되지 않았습니다."}

        today = datetime.now().strftime("%Y-%m-%d")

        params = {
            "action": "dailyPriceByCategoryList",
            "p_product_cls_code": "02",  # 소매
            "p_item_code": product_code,
            "p_country_code": region_code,
            "p_regday": today,
            "p_convert_kg_yn": "Y",
            "p_cert_key": self.api_key,
            "p_cert_id": self.cert_id,
            "p_returntype": "json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=10.0)
            return response.json()

    # KAMIS 주요 품목 코드
    PRODUCT_CODES = {
        "쌀": "111",
        "배추": "211",
        "무": "212",
        "양파": "213",
        "마늘": "214",
        "대파": "215",
        "고추": "221",
        "토마토": "225",
        "딸기": "226",
        "사과": "411",
        "배": "412",
        "포도": "413",
        "감귤": "414",
        "감자": "312",
        "고구마": "313",
    }


class NongsaroCollector:
    """농사로 API 기반 농업 기술 정보 수집"""

    BASE_URL = "http://api.nongsaro.go.kr/service"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""

    async def search_farming_tech(self, keyword: str) -> dict:
        """농업 기술 정보 검색"""
        if not self.api_key:
            return {"status": "error", "message": "농사로 API 키가 설정되지 않았습니다."}

        params = {
            "apiKey": self.api_key,
            "sType": "sTxt",
            "sText": keyword,
            "numOfRows": 10,
            "pageNo": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/farmTechInfo/farmTechList",
                params=params,
                timeout=10.0,
            )
            return response.json()

    async def get_pest_info(self, crop_name: str) -> dict:
        """작물별 병해충 정보 조회"""
        if not self.api_key:
            return {"status": "error", "message": "농사로 API 키가 설정되지 않았습니다."}

        params = {
            "apiKey": self.api_key,
            "sType": "sKnm",
            "sText": crop_name,
            "numOfRows": 20,
            "pageNo": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/pestInfo/pestList",
                params=params,
                timeout=10.0,
            )
            return response.json()
