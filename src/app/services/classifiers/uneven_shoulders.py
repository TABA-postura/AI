from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "UNEQUAL_SHOULDERS"


def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    한쪽 어깨 기울임(좌우 어깨 높이 차이) 감지 분류기.
    2단계에서는 항상 위반 아님으로 반환한다.
    """
    # TODO: shoulder_height_delta 메트릭 기반으로 구현
    return ok(CODE)
