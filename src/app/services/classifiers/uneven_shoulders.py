from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "UNEQUAL_SHOULDERS"

# 어깨 높이 차이가 프레임 높이의 5% 이상이면 경고로 본다.
THRESHOLD = 0.04  # 6%

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    왼/오 어깨 y좌표 차이 기반으로 한쪽 어깨 기울임 감지.

    metrics["shoulder_height_diff"]:
      - detector + metrics에서 계산한 y좌표 차이 절대값 (0~1)
    """
    value = metrics.get("shoulder_height_diff")
    if value is None:
        # 메트릭이 없으면 판단 불가 -> 일단 ok 처리
        return ok(CODE)

    is_violation = value > THRESHOLD
    if not is_violation:
        return ok(CODE)

    # threshold를 넘는 정도에 따라 confidence를 0~1로 스케일링
    # 예) 0.03에서 시작해서 0.13 이상이면 1.0
    confidence = min(1.0, max(0.0, (value - THRESHOLD) / 0.1))
    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)
