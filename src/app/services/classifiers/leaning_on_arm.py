from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "LEANING_ON_ARM"

# 손-얼굴 거리 기준 (0~1, 작을수록 얼굴에 가깝다고 가정)
# 실제 데이터에 맞춰 0.3~0.5 사이에서 튜닝해 볼 것.
HAND_FACE_THRESHOLD = 0.5

# 팔 높이 비대칭 기준 (0~1, 값이 클수록 한쪽 팔이 더 높음)
# elbow_height_diff / wrist_height_diff 둘 중 하나라도 이 값 이상이면
# "한쪽 팔이 위로 많이 올라와 있다"고 판단.
HEIGHT_DIFF_THRESHOLD = 0.02

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    한쪽 팔로 턱/머리를 괴는 자세 감지.

    - hand_face_dist_left/right: 코와 각 손목 사이의 거리 (0~1, 작을수록 얼굴에 가까움)
    - elbow_height_diff / wrist_height_diff: 좌/우 팔 높이 차이 (0~1, 절대값이 클수록 한쪽 팔이 높음)

    전략:
    1) 손-얼굴 거리가 충분히 가까운 손이 있고,
    2) 팔 높이 비대칭이 어느 정도 이상이면
       → LEANING_ON_ARM 위반으로 본다.
    """

    # 1) 손-얼굴 거리 처리
    dist_left = metrics.get("hand_face_dist_left")
    dist_right = metrics.get("hand_face_dist_right")

    if dist_left is None and dist_right is None:
        # 손목 좌표 자체를 못 잡은 경우 → 판단 보류 (OK)
        return ok(CODE)

    d_candidates = []
    if dist_left is not None:
        d_candidates.append(float(dist_left))
    if dist_right is not None:
        d_candidates.append(float(dist_right))

    nearest = min(d_candidates)

    # 2) 팔 높이 비대칭 처리
    elbow_diff = metrics.get("elbow_height_diff")
    wrist_diff = metrics.get("wrist_height_diff")

    height_flag = False
    max_height_val = 0.0

    for v in (elbow_diff, wrist_diff):
        if v is not None:
            v_abs = abs(float(v))
            max_height_val = max(max_height_val, v_abs)
            if v_abs > HEIGHT_DIFF_THRESHOLD:
                height_flag = True

    # 팔 높이 비대칭 조건이 만족되지 않으면 팔 지지 자세로 보지 않는다.
    if not height_flag:
        return ok(CODE)

    # 손-얼굴 거리가 충분히 가까운 경우에만 팔 지지 자세로 본다.
    if nearest > HAND_FACE_THRESHOLD:
        return ok(CODE)

    # 여기까지 왔으면 "손이 얼굴 근처에 있고, 한쪽 팔이 꽤 올라가 있는 상태"

    # 가까울수록 + 팔 높이 차이가 클수록 confidence ↑

    # (1) 거리 기반 severity: 0~1
    dist_severity = (HAND_FACE_THRESHOLD - nearest) / max(HAND_FACE_THRESHOLD, 1e-6)
    dist_severity = max(0.0, min(1.0, dist_severity))

    # (2) 팔 높이 기반 severity: 0~1
    HEIGHT_STRONG = HEIGHT_DIFF_THRESHOLD * 2.5  # 이 이상이면 "팔로 지탱" 정도로 본다.
    height_severity = (max_height_val - HEIGHT_DIFF_THRESHOLD) / max(
        HEIGHT_STRONG - HEIGHT_DIFF_THRESHOLD, 1e-6
    )
    height_severity = max(0.0, min(1.0, height_severity))

    # (3) 두 severity를 반반 섞어서 confidence 계산
    combined = 0.5 * dist_severity + 0.5 * height_severity
    confidence = 0.3 + 0.7 * combined

    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)