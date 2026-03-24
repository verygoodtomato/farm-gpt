import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm.chat_service import chat_service
from app.services.rag.rag_service import rag_service

router = APIRouter()


@router.post("/")
async def chat(request: ChatRequest):
    """RAG 기반 농업 컨설팅 챗봇 엔드포인트"""
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    if request.use_rag:
        return await _rag_chat(messages, request.stream)
    else:
        return await _direct_chat(messages, request.stream)


async def _rag_chat(messages: list[dict], stream: bool):
    """RAG 기반 응답"""
    if stream:
        try:
            generator, sources = await rag_service.chat_stream(messages)
            return StreamingResponse(
                _stream_rag_response(generator, sources),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        except Exception as e:
            # ChromaDB 연결 실패 시 직접 LLM으로 폴백
            return await _direct_chat(messages, stream)

    try:
        result = await rag_service.chat(messages)
        return {
            "content": result["content"],
            "sources": result["sources"],
            "search_results_count": result["search_results_count"],
        }
    except Exception:
        content = await chat_service.chat(messages)
        return ChatResponse(content=content)


async def _direct_chat(messages: list[dict], stream: bool):
    """LLM 직접 응답 (RAG 없이)"""
    if stream:
        return StreamingResponse(
            _stream_response(messages),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    content = await chat_service.chat(messages)
    return ChatResponse(content=content)


async def _stream_rag_response(generator, sources: list[str]):
    """RAG SSE 스트리밍 응답"""
    try:
        # 출처 정보 먼저 전송
        source_data = json.dumps({"sources": sources}, ensure_ascii=False)
        yield f"data: {source_data}\n\n"

        async for chunk in generator:
            data = json.dumps({"content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"data: {error_data}\n\n"


async def _stream_response(messages: list[dict]):
    """SSE 스트리밍 응답 생성"""
    try:
        async for chunk in chat_service.chat_stream(messages):
            data = json.dumps({"content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"data: {error_data}\n\n"


@router.get("/health")
async def chat_health():
    return {"status": "chat service healthy"}
