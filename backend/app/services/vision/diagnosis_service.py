"""작물 병해충 이미지 진단 서비스 - YOLOv8 + Claude Vision"""

import base64
import io
from pathlib import Path
from typing import Optional

import anthropic
from PIL import Image

from app.core.config import get_settings

settings = get_settings()

# 지원 작물 및 주요 병해충 매핑
CROP_DISEASES = {
    "딸기": {
        "diseases": [
            "잿빛곰팡이병", "흰가루병", "탄저병", "시들음병", "역병",
            "세균모무늬병", "바이러스병",
        ],
        "pests": ["점박이응애", "총채벌레", "진딧물", "작은뿌리파리"],
    },
    "토마토": {
        "diseases": [
            "잎곰팡이병", "역병", "황화잎말림바이러스", "풋마름병",
            "흰가루병", "겹무늬병",
        ],
        "pests": ["담배가루이", "아메리카잎굴파리", "총채벌레", "온실가루이"],
    },
    "파프리카": {
        "diseases": [
            "역병", "잿빛곰팡이병", "세균성점무늬병", "바이러스병(TSWV)",
            "흰가루병",
        ],
        "pests": ["총채벌레", "진딧물", "온실가루이", "점박이응애"],
    },
    "고추": {
        "diseases": [
            "탄저병", "역병", "바이러스병", "세균성점무늬병", "흰가루병",
        ],
        "pests": ["총채벌레", "진딧물", "담배나방", "점박이응애"],
    },
    "배추": {
        "diseases": [
            "무름병", "노균병", "균핵병", "검은썩음병",
        ],
        "pests": ["배추흰나비", "진딧물", "파밤나방", "배추좀나방"],
    },
    "사과": {
        "diseases": [
            "갈색무늬병", "탄저병", "점무늬낙엽병", "붉은별무늬병", "겹무늬썩음병",
        ],
        "pests": ["사과굴나방", "복숭아심식나방", "진딧물", "응애류"],
    },
}

VISION_DIAGNOSIS_PROMPT = """당신은 작물 병해충 이미지 진단 전문가입니다.

이미지를 분석하여 다음 정보를 제공하세요:

## 분석 형식

### 1. 진단 결과
- **병해충명**: (가장 가능성 높은 병해충)
- **신뢰도**: 높음/중간/낮음
- **카테고리**: 곰팡이병 / 세균병 / 바이러스병 / 해충 / 생리장해 / 정상

### 2. 증상 분석
- 관찰되는 주요 증상을 구체적으로 기술
- 잎, 줄기, 과실, 뿌리 등 부위별 증상

### 3. 방제 방법
- **즉시 조치**: 지금 바로 해야 할 것
- **약제 방제**: 추천 약제 및 사용법
- **생물학적 방제**: 천적 활용 등
- **환경 관리**: 온도, 습도 조절 등

### 4. 예방 대책
- 재발 방지를 위한 관리 방법
- 주의사항

{crop_context}

정확하지 않은 경우 "정밀 진단이 필요합니다"라고 밝히고, 가까운 농업기술센터 방문을 권장하세요.
"""


class DiagnosisService:
    """작물 병해충 진단 서비스"""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def diagnose_image(
        self,
        image_data: bytes,
        crop_type: Optional[str] = None,
        additional_info: Optional[str] = None,
    ) -> dict:
        """이미지 기반 병해충 진단 (Claude Vision API)"""

        # 이미지 전처리
        image = Image.open(io.BytesIO(image_data))

        # 큰 이미지 리사이즈 (최대 1024px)
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        # base64 인코딩
        buffer = io.BytesIO()
        img_format = "JPEG"
        if image.mode == "RGBA":
            img_format = "PNG"
        image.save(buffer, format=img_format)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        media_type = f"image/{img_format.lower()}"

        # 작물별 컨텍스트 구성
        crop_context = ""
        if crop_type and crop_type in CROP_DISEASES:
            info = CROP_DISEASES[crop_type]
            crop_context = f"""
참고: 이 작물은 **{crop_type}**입니다.
주요 병해: {', '.join(info['diseases'])}
주요 해충: {', '.join(info['pests'])}
"""

        system_prompt = VISION_DIAGNOSIS_PROMPT.format(crop_context=crop_context)

        # 사용자 메시지 구성
        user_content = []
        user_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_image,
            },
        })

        text_prompt = "이 작물 이미지를 분석하여 병해충을 진단해주세요."
        if crop_type:
            text_prompt = f"이 {crop_type} 이미지를 분석하여 병해충을 진단해주세요."
        if additional_info:
            text_prompt += f"\n추가 정보: {additional_info}"

        user_content.append({"type": "text", "text": text_prompt})

        # Claude Vision API 호출
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        diagnosis_text = response.content[0].text

        return {
            "diagnosis": diagnosis_text,
            "crop_type": crop_type,
            "image_size": f"{image.size[0]}x{image.size[1]}",
            "model": self.model,
        }

    async def diagnose_text(
        self,
        crop_type: str,
        symptoms: str,
    ) -> str:
        """텍스트 기반 병해충 진단"""
        crop_context = ""
        if crop_type in CROP_DISEASES:
            info = CROP_DISEASES[crop_type]
            crop_context = f"""
작물: {crop_type}
이 작물의 주요 병해: {', '.join(info['diseases'])}
이 작물의 주요 해충: {', '.join(info['pests'])}
"""

        system_prompt = VISION_DIAGNOSIS_PROMPT.format(crop_context=crop_context)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"작물: {crop_type}\n증상: {symptoms}\n\n위 증상을 분석하여 병해충을 진단해주세요.",
                }
            ],
        )

        return response.content[0].text

    def get_supported_crops(self) -> dict:
        """지원 작물 및 병해충 목록"""
        return CROP_DISEASES


diagnosis_service = DiagnosisService()
