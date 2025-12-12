from fastapi import APIRouter, UploadFile, File, Form
from ...services import pipeline, tracker, calibration
from ..schemas import AnalyzeResponse

from tensorflow.keras.models import load_model
import numpy as np
import tensorflow as tf

# 모델 로드
model = load_model('forward_head_model.h5')

# 모델 예측 함수
def predict_posture(image_bytes: bytes) -> str:
    image = preprocess_image(image_bytes)  # 이미지를 전처리

    prediction = model.predict(image)
    confidence = np.max(prediction)  # 모델 예측의 신뢰도
    
    # 예측 클래스 확인
    prediction_class = np.argmax(prediction)
    print("Prediction class:", prediction_class)
    print("Model confidence:", confidence)
    
    # 신뢰도 기준으로 예측 결과를 결정
    if confidence < 0.7:  # 신뢰도가 0.7 이상일 때만 예측을 받아들임
        return "UNKNOWN"  # 신뢰도가 낮으면 'UNKNOWN' 처리

    if prediction_class == 1:  # 1이 "FORWARD_HEAD"에 해당한다고 가정
        return "FORWARD_HEAD"
    else:
        return "GOOD"

# 이미지 전처리 함수
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = tf.image.decode_jpeg(image_bytes, channels=3)
    img = tf.image.resize(img, (224, 224))  # 모델 입력 크기에 맞게 리사이즈
    img = np.expand_dims(img, axis=0)  # 배치 차원 추가
    img = img / 255.0  # 정규화
    return img

# FastAPI 라우터 코드
router = APIRouter(prefix="/posture", tags=["posture"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_posture(
    sessionId: int = Form(...),
    reset: bool = Form(False),
    file: UploadFile = File(...),
):
    # 재설정 요청이면 tracker & calibration 상태 초기화
    if reset:
        tracker.reset()
        calibration.reset()

    image_bytes = await file.read()

    # 규칙 기반 분석 (기존대로 진행)
    result = pipeline.run(
        image_bytes=image_bytes,
        session_id=sessionId,
        reset=reset,
    )

    # 규칙 기반으로 "GOOD"이라면 모델 예측 생략
    if result['state'] == "GOOD":
        return result

    # 규칙 기반으로 거북목 판별 안되면 모델로 검증
    model_based_result = predict_posture(image_bytes)

    # 모델 예측이 거북목이라면, 결과 반영
    if model_based_result == "FORWARD_HEAD":
        result["state"] = "WARN"
        result["violations"].append("FORWARD_HEAD")

    return result