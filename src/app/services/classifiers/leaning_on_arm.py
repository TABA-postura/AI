from typing import Dict, Any

from .base import ClassificationResult, ok

CODE = "LEANING_ON_ARM"

# 손-얼굴 거리(threshold)
# 얼굴 크기(face_scale_raw)가 대략 0.1~0.2 정도 나올 때,
# 0.18 이하면 '턱/뺨 근처까지 올라온 손' 정도로 본다.
HAND_FACE_THRESHOLD = 0.18

def classify(metrics: Dict[str, Any]) -> ClassificationResult:
    """
    한쪽 손/팔 하단부(손목)가 얼굴 근처까지 올라와 있는지로
    '팔로 턱/머리를 괴고 있는 자세'를 추정한다.

    - hand_face_dist_left/right: 코와 각 손목 사이의 거리 (0~1, 프레임 비율)
      값이 작을수록 얼굴에 가깝다.
    """
    dist_left = metrics.get("hand_face_dist_left")
    dist_right = metrics.get("hand_face_dist_right")

    # 둘 다 없는 경우 → 판단 불가
    if dist_left is None and dist_right is None:
        return ok(CODE)

    # 한쪽이라도 거리 정보가 있으면 그 중 더 가까운 쪽 사용
    d_candidates = []
    if dist_left is not None:
        d_candidates.append(dist_left)
    if dist_right is not None:
        d_candidates.append(dist_right)

    nearest = min(d_candidates)

    # 얼굴에서 너무 멀면 팔 지지 자세가 아닌 것으로 본다.
    is_violation = nearest < HAND_FACE_THRESHOLD
    if not is_violation:
        return ok(CODE)

    # 가까울수록 confidence ↑ (0에 가까운 값일수록 확신 강함)
    # threshold에서 0까지 선형으로 0.3~1.0 사이로 스케일링
    norm = max(0.0, (HAND_FACE_THRESHOLD - nearest) / HAND_FACE_THRESHOLD)  # 0~1
    confidence = 0.3 + 0.7 * norm

    return ClassificationResult(code=CODE, is_violation=True, confidence=confidence)