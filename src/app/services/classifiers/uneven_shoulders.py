from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "UNEQUAL_SHOULDERS"

# baseline 대비 어깨 높이 차이가 이 이상이면 위반
DELTA_THRESHOLD = 0.01   # 1% 이상 증가 시

# baseline 없을 때 절대 차이 기준
ABS_THRESHOLD = 0.06     # 6% 이상이면 위반

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    왼/오 어깨 y좌표 차이 기반으로 한쪽 어깨 기울임 감지.

    - shoulder_height_delta: baseline 대비 y좌표 차이 증가량 (0~1)
    - shoulder_height_diff: 절대 y좌표 차이 (0~1)
    """
    diff = metrics.get("shoulder_height_diff")
    delta = metrics.get("shoulder_height_delta")

    # 1) baseline이 있으면 delta 기준
    if delta is not None:
        is_violation = delta > DELTA_THRESHOLD
        if not is_violation:
            return ok(CODE)

        norm = max(0.0, min(1.0, (delta - DELTA_THRESHOLD) / 0.1))
        confidence = 0.3 + 0.7 * norm
        return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)

    # 2) fallback: baseline 없으면 절대값 기준
    if diff is None:
        return ok(CODE)

    is_violation = diff > ABS_THRESHOLD
    if not is_violation:
        return ok(CODE)

    norm = max(0.0, min(1.0, (diff - ABS_THRESHOLD) / 0.1))
    confidence = 0.3 + 0.7 * norm
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)