from typing import Dict, Any
from .base import ClassificationResult, ok

CODE = "FORWARD_HEAD"

# baseline 대비 목이 이 정도 이상 앞으로 나오면 거북목으로 본다.
# (delta 값은 0~1 범위라고 가정)
DELTA_THRESHOLD = 0.03   # 이 이상이면 "조금 앞으로 나옴"
DELTA_STRONG = 0.05      # 이 이상이면 "꽤 심한 거북목"

# baseline 없는 경우를 위한 절대값 기준
ABS_THRESHOLD = 0.23     # forward_head_amount가 이 이상이면 위반
ABS_STRONG = ABS_THRESHOLD + 0.12  # 아주 심한 영역 (대략 0.35 근처)

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    어깨 대비 머리가 앞으로 나온 정도 기반 거북목 감지.

    1순위: calibration에서 계산된 forward_head_delta(개인 baseline 대비 변화량)를 사용하고,
    2순위: baseline이 없을 때만 forward_head_amount(절대값)를 사용한다.
    """
    value = metrics.get("forward_head_amount")
    delta = metrics.get("forward_head_delta")
    face_delta = metrics.get("face_scale_delta")

    # 1) baseline이 있는 경우: delta 기준
    if delta is not None:
        # baseline에서 거의 안 벗어났으면 GOOD
        if delta <= DELTA_THRESHOLD:
            return ok(CODE)

        # 얼굴이 기준보다 많이 뒤로 가는 방향이라면(zoom out) 거북목으로 보지 않음
        if face_delta is not None and face_delta < -0.01:
            return ok(CODE)

        # delta가 DELTA_THRESHOLD ~ DELTA_STRONG 사이일 때 0~1로 정규화
        if delta >= DELTA_STRONG:
            severity = 1.0
        else:
            severity = (delta - DELTA_THRESHOLD) / max(DELTA_STRONG - DELTA_THRESHOLD, 1e-6)

        severity = max(0.0, min(1.0, severity))
        confidence = 0.3 + 0.7 * severity

        return ClassificationResult(
            code=CODE,
            is_violation=True,
            confidence=confidence,
        )

    # 2) baseline이 없는 경우: 절대값 기준 fallback
    if value is None:
        return ok(CODE)

    if value <= ABS_THRESHOLD:
        return ok(CODE)

    # value가 ABS_THRESHOLD ~ ABS_STRONG 사이일 때 0~1로 정규화
    severity = int((value - ABS_THRESHOLD) / max(ABS_STRONG - ABS_THRESHOLD, 1e-6))  # 정수로 변환
    severity = max(0, min(1, severity))  # 0~1 범위로 유지
    confidence = 0.3 + 0.7 * severity  # confidence는 실수일 수 있음

    return ClassificationResult(
        code=CODE,
        is_violation=True,
        confidence=confidence,
    )