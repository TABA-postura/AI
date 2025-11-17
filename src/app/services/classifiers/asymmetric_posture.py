from typing import Dict, Any
from math import fabs

from .base import ClassificationResult, ok

CODE = "ASYMMETRIC_POSTURE"

# '나쁜 신호'가 몇 개 이상 동시에 켜지면 비대칭 자세로 본다.
MIN_FLAGS = 2

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    어깨/머리 관련 여러 메트릭이 동시에 나쁘게 나올 때
    '전체적으로 비대칭한 자세'로 태깅하는 보조 classifier.
    """
    flags = 0

    shoulder_diff = metrics.get("shoulder_height_diff")
    if shoulder_diff is not None and shoulder_diff > 0.06:
        flags += 1

    shoulder_angle = metrics.get("shoulder_line_angle_deg")
    if shoulder_angle is not None and fabs(shoulder_angle) > 10.0:
        flags += 1

    head_angle = metrics.get("head_line_angle_deg")
    if head_angle is not None and fabs(head_angle) > 10.0:
        flags += 1

    if flags < MIN_FLAGS:
        return ok(CODE)

    # flags가 많을수록 confidence를 높게
    confidence = min(1.0, 0.3 * flags)
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)