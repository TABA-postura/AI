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

    baseline 기반 delta가 있으면 우선 사용하고, 없으면 raw 값을 사용한다.
    """
    flags = 0

    # 1) 어깨 높이 비대칭
    diff_delta = metrics.get("shoulder_height_delta")
    diff = metrics.get("shoulder_height_diff")
    if diff_delta is not None:
        if diff_delta > 0.02:  # baseline 대비 2%p 이상
            flags += 1
    elif diff is not None and diff > 0.06:
        flags += 1

    # 2) 어깨선 기울기 비대칭
    tilt_delta = metrics.get("shoulder_tilt_delta")
    shoulder_angle = metrics.get("shoulder_line_angle_deg")
    if tilt_delta is not None:
        if fabs(tilt_delta) > 5.0:
            flags += 1
    elif shoulder_angle is not None and fabs(shoulder_angle) > 10.0:
        flags += 1

    # 3) 머리 기울기 비대칭
    head_tilt_delta = metrics.get("head_tilt_delta")
    head_angle = metrics.get("head_line_angle_deg")
    if head_tilt_delta is not None:
        if fabs(head_tilt_delta) > 5.0:
            flags += 1
    elif head_angle is not None and fabs(head_angle) > 10.0:
        flags += 1

    if flags < MIN_FLAGS:
        return ok(CODE)

    # flags가 많을수록 confidence를 높게
    confidence = min(1.0, 0.3 * flags)
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)