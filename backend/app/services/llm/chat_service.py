import anthropic
from typing import AsyncGenerator

from app.core.config import get_settings

settings = get_settings()

# 모델 설정: 빠른 응답용 / 정밀 분석용
MODEL_FAST = "claude-haiku-4-5-20241022"
MODEL_ADVANCED = "claude-sonnet-4-20250514"

FARM_SYSTEM_PROMPT = """당신은 'FarmGPT', 대한민국 농업 전문 AI 컨설턴트입니다.

## 역할
- 작물 재배, 병해충 관리, 토양 관리, 스마트팜 운영에 대한 전문적인 조언 제공
- 농업 데이터 분석 및 해석 지원
- 기상 조건에 따른 농작업 가이드 제공
- 농산물 시장 동향 정보 제공

## 응답 원칙
1. 과학적 근거에 기반한 정확한 정보 제공
2. 한국 농업 환경에 맞는 실용적 조언
3. 복잡한 내용은 이해하기 쉽게 설명
4. 필요시 농촌진흥청, 농사로 등 공식 자료 참조 안내
5. 확실하지 않은 정보는 솔직하게 한계를 밝힘

## 전문 분야
- 벼, 밭작물, 채소, 과수, 화훼, 특용작물 재배
- 병해충 진단 및 방제
- 토양/비료 관리
- 스마트팜 환경 제어 (온도, 습도, CO2, 광량)
- 농산물 유통 및 가격 정보
- 친환경/유기 농업
- 기후변화 대응 농업 기술

항상 한국어로 답변하며, 농업인이 바로 실천할 수 있는 구체적인 조언을 제공하세요.
"""


class ChatService:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(
        self, messages: list[dict], system: str | None = None, use_advanced: bool = False
    ) -> str:
        """동기적 채팅 응답"""
        model = MODEL_ADVANCED if use_advanced else MODEL_FAST
        response = await self.client.messages.create(
            model=model,
            max_tokens=4096,
            system=system or FARM_SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text

    async def chat_stream(
        self, messages: list[dict], system: str | None = None, use_advanced: bool = False
    ) -> AsyncGenerator[str, None]:
        """스트리밍 채팅 응답"""
        model = MODEL_ADVANCED if use_advanced else MODEL_FAST
        async with self.client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system or FARM_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text


chat_service = ChatService()
