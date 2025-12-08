from typing import Dict, Any
from math import fabs

from .base import ClassificationResult, ok

CODE = "UPPER_BODY_TILT"

# baseline 대비 어깨선 기울기가 이 이상이면 위반
DELTA_THRESHOLD_DEG = 2.0   # 2도 이상 추가 기울기

# baseline 없을 때 절대 각도 기준
ABS_THRESHOLD_DEG = 8.0

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    양 어깨를 잇는 선의 기울기(각도) 기반으로 상체 좌/우 기울기 감지.

    - shoulder_tilt_delta: baseline 대비 기울기 증가량 (deg)
    - shoulder_line_angle_deg: LEFT_SHOULDER -> RIGHT_SHOULDER 선의 각도 (deg)
    """
    angle = metrics.get("shoulder_line_angle_deg")
    delta = metrics.get("shoulder_tilt_delta")

    # 1) baseline이 있으면 delta 기준
    if delta is not None:
        tilt_delta = fabs(delta)
        is_violation = tilt_delta > DELTA_THRESHOLD_DEG
        if not is_violation:
            return ok(CODE)

        norm = max(0.0, min(1.0, (tilt_delta - DELTA_THRESHOLD_DEG) / 10.0))
        confidence = 0.3 + 0.7 * norm
        return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)

    # 2) fallback: baseline 없으면 절대 각도 기준
    if angle is None:
        return ok(CODE)

    tilt = fabs(angle)
    is_violation = tilt > ABS_THRESHOLD_DEG
    if not is_violation:
        return ok(CODE)

    norm = max(0.0, min(1.0, (tilt - ABS_THRESHOLD_DEG) / 10.0))
    confidence = 0.3 + 0.7 * norm
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)