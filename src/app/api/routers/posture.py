from fastapi import APIRouter, UploadFile, File, Form

from ...services import pipeline, tracker, calibration
from ..schemas import AnalyzeResponse

router = APIRouter(prefix="/posture", tags=["posture"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_posture(
    userId: int = Form(...),
    sessionId: int = Form(...),
    reset: bool = Form(False),
    file: UploadFile = File(...),
):
    # 재설정 요청이면 tracker & calibration 상태 초기화
    if reset:
        tracker.reset()
        calibration.reset()

    """
    - React가 FormData로 보내는 구조 예시:
      formData.append("userId", userId);
      formData.append("sessionId", sessionId);
      formData.append("file", imageBlob);
    """
    image_bytes = await file.read()

    result = pipeline.run(
        image_bytes=image_bytes,
        user_id=userId,
        session_id=sessionId,
    )

    return result