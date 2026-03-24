"""RAG 서비스 - 벡터 검색 + LLM 결합"""

from typing import AsyncGenerator, Optional

from app.services.rag.vector_store import vector_store
from app.services.llm.chat_service import ChatService

RAG_SYSTEM_PROMPT = """당신은 'FarmGPT', 대한민국 농업 전문 AI 컨설턴트입니다.

## 역할
- 작물 재배, 병해충 관리, 토양 관리, 스마트팜 운영에 대한 전문적인 조언 제공
- 농업 데이터 분석 및 해석 지원
- 기상 조건에 따른 농작업 가이드 제공

## 중요 지침
1. 아래 제공된 [참고 자료]를 **우선적으로** 활용하여 답변하세요.
2. 참고 자료에 있는 구체적인 수치(온도, 습도, 농도 등)를 정확히 인용하세요.
3. 참고 자료만으로 부족한 경우, 일반 농업 지식으로 보충하되 "참고 자료 외 일반 지식" 임을 밝히세요.
4. 확실하지 않은 정보는 "확인이 필요합니다"라고 솔직하게 밝히세요.
5. 한국 농업 환경에 맞는 실용적 조언을 제공하세요.
6. 농업인이 바로 실천할 수 있는 구체적인 수치와 방법을 포함하세요.

## 답변 형식
- 핵심 내용을 먼저 제시하고 세부 사항을 보충
- 수치 데이터는 표나 목록으로 정리
- 실행 가능한 조치 사항을 구체적으로 제시
- 관련 주의사항이나 팁을 추가

항상 한국어로 답변합니다.
"""


class RAGService:
    """RAG(Retrieval-Augmented Generation) 서비스"""

    def __init__(self):
        self.vector_store = vector_store
        self.llm = ChatService()

    def _build_context(self, search_results: list[dict]) -> str:
        """검색 결과를 컨텍스트 문자열로 변환"""
        if not search_results:
            return ""

        context_parts = ["[참고 자료]"]
        for i, result in enumerate(search_results, 1):
            source = result["source"]
            relevance = result["relevance"]
            content = result["content"]
            context_parts.append(
                f"\n--- 자료 {i} (출처: {source}, 관련도: {relevance:.0%}) ---\n{content}"
            )

        return "\n".join(context_parts)

    def _build_messages(
        self,
        user_messages: list[dict],
        context: str,
    ) -> list[dict]:
        """RAG 컨텍스트가 포함된 메시지 생성"""
        messages = []

        # 이전 대화 히스토리 유지
        for msg in user_messages[:-1]:
            messages.append(msg)

        # 마지막 사용자 메시지에 컨텍스트 추가
        last_message = user_messages[-1]
        if context:
            enhanced_content = f"""{context}

---
[사용자 질문]
{last_message['content']}

위 참고 자료를 활용하여 질문에 답변해주세요."""
        else:
            enhanced_content = last_message["content"]

        messages.append({"role": "user", "content": enhanced_content})
        return messages

    async def chat(
        self,
        messages: list[dict],
        n_results: int = 5,
        min_relevance: float = 0.3,
    ) -> dict:
        """RAG 기반 채팅 (동기 응답)"""
        # 1. 사용자 질문으로 관련 문서 검색
        user_query = messages[-1]["content"]
        search_results = self.vector_store.search(user_query, n_results=n_results)

        # 관련도 필터링
        filtered_results = [r for r in search_results if r["relevance"] >= min_relevance]

        # 2. 컨텍스트 구성
        context = self._build_context(filtered_results)

        # 3. LLM에 전달
        enhanced_messages = self._build_messages(messages, context)
        response = await self.llm.chat(enhanced_messages, system=RAG_SYSTEM_PROMPT)

        # 4. 출처 정보 포함하여 반환
        sources = list({r["source"] for r in filtered_results})

        return {
            "content": response,
            "sources": sources,
            "search_results_count": len(filtered_results),
        }

    async def chat_stream(
        self,
        messages: list[dict],
        n_results: int = 5,
        min_relevance: float = 0.3,
    ) -> tuple[AsyncGenerator[str, None], list[str]]:
        """RAG 기반 채팅 (스트리밍 응답)"""
        # 1. 사용자 질문으로 관련 문서 검색
        user_query = messages[-1]["content"]
        search_results = self.vector_store.search(user_query, n_results=n_results)
        filtered_results = [r for r in search_results if r["relevance"] >= min_relevance]

        # 2. 컨텍스트 구성
        context = self._build_context(filtered_results)

        # 3. LLM 스트리밍
        enhanced_messages = self._build_messages(messages, context)
        sources = list({r["source"] for r in filtered_results})

        async def stream():
            async for chunk in self.llm.chat_stream(enhanced_messages, system=RAG_SYSTEM_PROMPT):
                yield chunk

        return stream(), sources

    def index_knowledge_base(self) -> dict:
        """지식베이스 인덱싱"""
        return self.vector_store.index_knowledge_base()

    def get_stats(self) -> dict:
        """RAG 시스템 통계"""
        return self.vector_store.get_stats()


rag_service = RAGService()
