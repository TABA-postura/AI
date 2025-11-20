from fastapi import APIRouter, UploadFile, File, Form

from ...services import pipeline

router = APIRouter(prefix="/posture", tags=["posture"])

@router.post("/analyze")
async def analyze_posture(
    userId: int = Form(...),
    sessionId: int = Form(...),
    file: UploadFile = File(...),
):
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