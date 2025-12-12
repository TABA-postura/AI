from fastapi import APIRouter, UploadFile, File, Form
from typing import List, Dict, Any

from ...services import pipeline, tracker, calibration
from ..schemas import AnalyzeResponse
from ...services.classifiers.forward_head import classify
import time

from tensorflow.keras.models import load_model
import numpy as np
import tensorflow as tf

# 모델 로드
model = load_model('forward_head_model.h5')

# 모델 예측 함수
def predict_posture(image_bytes: bytes) -> str:
    image = preprocess_image(image_bytes)  # 이미지를 전처리
    prediction = model.predict(image)
    
    # 예측 결과가 거북목인지 판단
    if prediction[0] >= 0.5:  # 0.5 이상의 확률이면 거북목으로 판별
        return "FORWARD_HEAD"
    return "GOOD"

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    이미지를 모델에 맞는 형식으로 전처리합니다.
    """
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
    # 규칙 기반 분석 (거북목을 규칙으로 판별)
    rule_based_result = classify({'forward_head_amount': 0.25, 'forward_head_delta': 0.04})  # 예시로 적당한 metrics 사용

    # 결과 결합
    final_violations = []

    # 초기화: severity를 0으로 설정
    severity = 0

    # 규칙 기반 분석에서 거북목 판별
    if rule_based_result.is_violation:
        severity = int(rule_based_result.confidence)  # 정수로 변환
        # severity가 0일 경우 1로 변경
        severity = max(severity, 1)

        final_violations.append({
            "code": rule_based_result.code,
            "severity": severity,
            "confidence": rule_based_result.confidence,
        })
    
    # 규칙 기반 분석에서 거북목이 아니라고 판단한 경우에만 모델 분석을 수행
    else:
        # 이미지 처리
        image_bytes = await file.read()

        # 모델 기반 분석 (거북목 분류)
        model_based_result = predict_posture(image_bytes)
        
        # 모델 결과의 신뢰도를 계산하여 결과 반영 여부 결정
        model_confidence = 0.7  # 예시: 모델의 신뢰도 (0 ~ 1 사이 값, 모델 예측 시 반환된 값)

        # 모델 기반 분석 결과 추가
        if model_based_result == "FORWARD_HEAD" and model_confidence >= 0.7:
            severity = 1.0  # 예시로 부여된 실수 값
            severity = int(severity)  # 정수로 변환
            severity = max(severity, 1)  # severity가 0일 경우 1로 변경

            final_violations.append({
                "code": "FORWARD_HEAD",
                "severity": severity,
                "confidence": 1.0,
            })

    # 상태 결정 (GOOD이 아니라면 WARN 처리)
    if not final_violations:
        state = "GOOD"
    else:
        state = "WARN"

    # 피드백 생성
    advices = generate_advices(final_violations)

    return {
        "state": state,
        "violations": [v["code"] for v in final_violations],
        "violation_details": final_violations,
        "advices": advices,
        "metrics": {},  # 메트릭 데이터 추가 가능
        "timestamp_ms": int(time.time() * 1000),
    }

def generate_advices(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    advices = []
    for violation in violations:
        if violation["code"] == "FORWARD_HEAD":
            advices.append({
                "code": "FORWARD_HEAD",
                "message": "거북목이 감지됐어요. 턱을 살짝 당기고, 머리가 어깨 위에 올라오도록 세워 주세요.",
                "content_id": "POSTURE_FORWARD_HEAD",
            })
        # 다른 위반 사항에 대한 피드백도 추가 가능
    return advices