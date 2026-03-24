from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from app.services.vision.diagnosis_service import diagnosis_service

router = APIRouter()


@router.post("/text")
async def diagnose_from_text(
    crop_type: str = Form(...),
    symptoms: str = Form(...),
):
    """텍스트 기반 작물 병해충 진단"""
    result = await diagnosis_service.diagnose_text(crop_type, symptoms)
    return {"diagnosis": result, "crop_type": crop_type}


@router.post("/image")
async def diagnose_from_image(
    file: UploadFile = File(...),
    crop_type: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
):
    """이미지 기반 작물 병해충 진단 (Claude Vision)"""
    # 파일 유효성 검사
    if not file.content_type or not file.content_type.startswith("image/"):
        return {"status": "error", "message": "이미지 파일만 업로드 가능합니다."}

    # 파일 크기 제한 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        return {"status": "error", "message": "파일 크기는 10MB 이하여야 합니다."}

    result = await diagnosis_service.diagnose_image(
        image_data=contents,
        crop_type=crop_type,
        additional_info=additional_info,
    )

    return result


@router.get("/crops")
async def get_supported_crops():
    """지원 작물 및 병해충 목록 조회"""
    return diagnosis_service.get_supported_crops()
