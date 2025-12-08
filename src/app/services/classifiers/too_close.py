from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "TOO_CLOSE"

# baseline 대비 얼굴 크기가 이 이상 커지면 '너무 가까움'으로 간주
DELTA_THRESHOLD = 0.01  # 1% 이상 증가

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    얼굴 크기(눈 사이 거리) 기반으로 화면과의 거리가 너무 가까운지 감지.
    - calibration이 적용된 후라면 face_scale_delta를 우선 사용.
    - baseline이 없는 경우에는 단순 raw 값 기준으로 대략적인 감지만 수행.
    """
    delta = metrics.get("face_scale_delta")
    if delta is not None:
        # baseline 대비 변화량 사용
        is_violation = delta > DELTA_THRESHOLD
        if not is_violation:
            return ok(CODE)

        confidence = min(1.0, max(0.0, (delta - DELTA_THRESHOLD) / 0.1))
        return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)

    # fallback: baseline이 아직 없으면 raw 값 기준으로 아주 대충만 본다.
    raw = metrics.get("face_scale_raw")
    if raw is None:
        return ok(CODE)

    # 0.2 이상이면 꽤 가까운 편이라고 가정 (환경에 따라 조정 필요)
    RAW_THRESHOLD = 0.2
    is_violation = raw > RAW_THRESHOLD
    if not is_violation:
        return ok(CODE)

    confidence = min(1.0, max(0.0, (raw - RAW_THRESHOLD) / 0.1))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)
