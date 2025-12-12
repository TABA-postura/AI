from fastapi import APIRouter, UploadFile, File, Form
from ...services import pipeline, tracker, calibration, exporter
from ..schemas import AnalyzeResponse

from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

import numpy as np
import tensorflow as tf
import json

MODEL_PATH = "my_model.h5"
LABEL_PATH = "class_indices.json"
MODEL_CONF_TH = 0.70  # 필요 시 조정

# 모델 로드
model = load_model(MODEL_PATH)

with open(LABEL_PATH, "r", encoding="utf-8") as f:
    class_indices = json.load(f)

if model.output_shape[-1] != len(class_indices):
    raise RuntimeError("my_model.h5 와 class_indices.json 클래스 수 불일치")

# index -> label
idx_to_label = {int(v): k for k, v in class_indices.items()}

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = tf.image.decode_jpeg(image_bytes, channels=3)
    img = tf.image.resize(img, (224, 224))
    img = tf.cast(img, tf.float32)
    img = preprocess_input(img)  # MobileNetV2 전용 전처리
    img = tf.expand_dims(img, axis=0)
    return img.numpy()

def predict_multiclass(image_bytes: bytes):
    x = preprocess_image(image_bytes)
    probs = model.predict(x, verbose=0)[0]     # shape: (num_classes,)
    top_idx = int(np.argmax(probs))
    top_prob = float(probs[top_idx])
    top_label = idx_to_label[top_idx]
    return top_label, top_prob

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

    # 규칙 기반 분석
    result = pipeline.run(
        image_bytes=image_bytes,
        session_id=sessionId,
        reset=reset,
    )

    # 규칙 기반 결과가 GOOD/UNKNOWN/ERROR면 그대로 반환
    if result["state"] in ("GOOD", "UNKNOWN", "ERROR"):
        try:
            exporter.publish_to_backend(session_id=sessionId, result=result)
        except Exception:
            pass
        return result

    violations = result.get("violations", [])

    top_label, top_prob = predict_multiclass(image_bytes)

    # 모델이 확신하고, GOOD이 아닐 때만 violations에 "추가"
    if top_prob >= MODEL_CONF_TH and top_label != "GOOD":
        if top_label not in violations:
            violations.append(top_label)

    # 방어적으로 정리(혹시라도 섞이면 제거)
    violations = [v for v in violations if v and v not in ("GOOD", "UNKNOWN")]

    result["violations"] = violations
    result["state"] = "WARN" if violations else "GOOD"

    # 최종 결과를 BE로 전송
    try:
        exporter.publish_to_backend(session_id=sessionId, result=result)
    except Exception:
        pass

    return result