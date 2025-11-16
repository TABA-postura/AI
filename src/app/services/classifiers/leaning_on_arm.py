from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "LEANING_ON_ARM"


def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    팔 지지 자세 감지 분류기.
    2단계에서는 항상 위반 아님으로 반환한다.
    """
    # TODO: shoulder_height_delta 메트릭 기반으로 구현
    return ok(CODE)
