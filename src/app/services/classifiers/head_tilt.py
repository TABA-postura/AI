from typing import Dict, Any
from math import fabs

from .base import ClassificationResult, ok

CODE = "HEAD_TILT"
THRESHOLD_DEG = 10.0  # 10도 이상 기울면 경고

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    머리 좌/우 기울기 감지 (귀-귀 선의 각도).
    """
    angle = metrics.get("head_line_angle_deg")
    if angle is None:
        return ok(CODE)

    tilt = fabs(angle)
    is_violation = tilt > THRESHOLD_DEG
    if not is_violation:
        return ok(CODE)

    # 8도에서 시작해서 18도 이상이면 confidence=1.0
    confidence = min(1.0, max(0.0, (tilt - THRESHOLD_DEG) / 10.0))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)
