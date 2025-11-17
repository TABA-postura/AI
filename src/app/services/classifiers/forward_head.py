from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "FORWARD_HEAD"
# 머리가 어깨 대비 이 정도 이상 앞으로 나오면 거북목으로 본다.
THRESHOLD = 0.25

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    어깨 대비 머리가 앞으로 나온 정도 기반 거북목 감지.
    metrics["forward_head_amount"]가 클수록 머리가 카메라 쪽으로 나와 있다고 본다.
    """
    value = metrics.get("forward_head_amount")
    if value is None:
        return ok(CODE)

    is_violation = value > THRESHOLD
    if not is_violation:
        return ok(CODE)

    confidence = min(1.0, max(0.0, (value - THRESHOLD) / 0.1))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)
