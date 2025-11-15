from fastapi import APIRouter, UploadFile, File

from app.services import pipeline

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    AI 서버 헬스 체크용 엔드포인트.
    BE나 FE에서 'AI 서버 살아 있나?' 확인할 때 사용.
    """
    return {"status": "ok"}

@router.post("/anlyze")
async def analyze_posture(image: UploadFile = File(...)):
    """
    단일 이미지에 대한 자세 분석 엔드포인트.

    2단계에서는 이미지 내용을 실제로 분석하지 않고,
    파이프라인을 한 번 태운 뒤 더미 결과를 반환한다.
    """
    image_bytes = await image.read()
    result = pipeline.run(image_bytes)
    return result