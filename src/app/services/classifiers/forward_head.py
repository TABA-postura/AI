from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "FORWAD_HEAD"
THRESHOLD = 0.12  # 어깨 대비 귀의 z 차이가 이 값 이상이면 거북목으로 봄

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    어깨 대비 머리가 앞으로 나온 정도 기반 거북목 감지.
    metrics["forward_head_z_diff"]가 클수록 머리가 카메라 쪽으로 나와 있다고 본다.
    """
    value = metrics.get("forward_head_z_diff")
    if value is None:
        return ok(CODE)

    is_violation = value > THRESHOLD
    if not is_violation:
        return ok(CODE)

    confidence = min(1.0, max(0.0, (value - THRESHOLD) / 0.1))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)
