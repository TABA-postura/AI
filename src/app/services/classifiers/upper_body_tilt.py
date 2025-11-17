from typing import Dict, Any
from math import fabs

from .base import ClassificationResult, ok

CODE = "UPPER_BODY_TILT"

# 어깨선 각도가 8도 이상 기울면 경고로 본다.
THRESHOLD_DEG = 8.0

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    양 어깨를 잇는 선의 기울기(각도) 기반으로 상체 좌/우 기울기 감지.

    metrics["shoulder_line_angle_deg"]:
      - LEFT_SHOULDER -> RIGHT_SHOULDER 선의 각도 (deg)
    """
    angle = metrics.get("shoulder_line_angle_deg")
    if angle is None:
        return ok(CODE)

    tilt = fabs(angle)  # 절대값 (좌/우 상관없이 얼마나 기울었는지만)
    is_violation = tilt > THRESHOLD_DEG
    if not is_violation:
        return ok(CODE)
    
        # 6도에서 시작해서 16도 이상이면 confidence=1.0
    confidence = min(1.0, max(0.0, (tilt - THRESHOLD_DEG) / 10.0))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)
