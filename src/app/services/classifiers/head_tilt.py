from typing import Dict, Any
from math import fabs

from .base import ClassificationResult, ok

CODE = "HEAD_TILT"

DELTA_THRESHOLD_DEG = 5.0
ABS_THRESHOLD_DEG = 10.0  # baseline 없을 때 절대 기준

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    머리 좌/우 기울기 감지 (귀-귀 선의 각도).

    - head_tilt_delta: baseline 대비 머리 기울기 증가량 (deg)
    - head_line_angle_deg: 귀-귀 선 각도 (deg)
    """
    angle = metrics.get("head_line_angle_deg")
    delta = metrics.get("head_tilt_delta")

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