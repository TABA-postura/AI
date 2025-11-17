from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "LEANING_ON_ARM"

# 팔꿈치/손목 높이 차이가 이 이상이면 한쪽 팔에 많이 기대는 것으로 추정
ELBOW_DIFF_THRESHOLD = 0.10
WRIST_DIFF_THRESHOLD = 0.10

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    팔꿈치/손목 높이 비대칭 정도로 '한쪽 팔에 기대는 자세'를 대략 감지.
    - keyboard/마우스 기본 자세에서도 팔 높이 차이가 조금 날 수 있으므로,
      threshold는 꽤 넉넉하게 잡는다.
    """
    elbow_diff = metrics.get("elbow_height_diff", 0.0) or 0.0
    wrist_diff = metrics.get("wrist_height_diff", 0.0) or 0.0

    value = max(elbow_diff, wrist_diff)
    is_violation = (elbow_diff > ELBOW_DIFF_THRESHOLD) and (
        wrist_diff > WRIST_DIFF_THRESHOLD
    )
    if not is_violation:
        return ok(CODE)

    confidence = min(1.0, max(0.0, (value - ELBOW_DIFF_THRESHOLD) / 0.15))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)