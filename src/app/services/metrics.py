from typing import Any, Dict, Optional
import math

def _get_landmarks(posture_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    detector.detect()가 반환한 dict에서 landmarks 부분만 꺼낸다.
    예상 형식: {"LEFT_SHOULDER": {"x": ..., "y": ..., ...}, ...}
    """
    raw = posture_data.get("landmarks") or {}
    if not isinstance(raw, dict):
        # 아직 detector가 dict로 안 넘기는 경우 방어용
        return {}
    return raw

def _get_point(
    landmarks: Dict[str, Dict[str, float]],
    name: str,
) -> Optional[Dict[str, float]]:
    """
    특정 이름의 포인트를 dict 형태로 가져온다.
    없거나 형식이 이상하면 None.
    """
    point = landmarks.get(name)
    if not isinstance(point, dict):
        return None
    return point

def _angle_deg(dx: float, dy: float) -> float:
    """
    (dx, dy) 벡터의 각도를 deg로 반환하고,
    [-90, 90] 범위로 접어서 '기울기'만 남긴다.
    """
    if dx == 0 and dy == 0:
        return 0.0

    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    # 180도 방향(←)도 기울기는 0도로 봐야 하므로 -90~90으로 접기
    if angle_deg > 90:
        angle_deg -= 180
    elif angle_deg < -90:
        angle_deg += 180

    return angle_deg

def compute(posture_data: Dict[str, Any]) -> Dict[str, float]:
    """
    자세 데이터(posture_data)에서 숫자 메트릭들을 계산한다.

    반환 예:
    {
        "shoulder_height_diff": 0.04,
        "shoulder_line_angle_deg": 7.2
        "shoulder_height_diff": 0.04,
        "shoulder_line_angle_deg": 7.2,
        "head_line_angle_deg": -5.3,
        "face_scale_raw": 0.18,
        "forward_head_z_diff": 0.12,
        "elbow_height_diff": 0.09,
        "wrist_height_diff": 0.11,
        ...
    }

    - shoulder_height_diff:
        LEFT/RIGHT_SHOULDER y좌표 차이의 절대값 (정규화된 비율, 0~1)
    - shoulder_line_angle_deg:
        왼쪽→오른쪽 어깨를 잇는 선의 기울기 (deg)
    """
    landmarks = _get_landmarks(posture_data)
    metrics: Dict[str, float] = {}

    # --- 공통으로 쓸 포인트들 미리 꺼내기 ---
    left_shoulder = _get_point(landmarks, "LEFT_SHOULDER")
    right_shoulder = _get_point(landmarks, "RIGHT_SHOULDER")

    left_ear = _get_point(landmarks, "LEFT_EAR")
    right_ear = _get_point(landmarks, "RIGHT_EAR")

    left_eye = _get_point(landmarks, "LEFT_EYE")
    right_eye = _get_point(landmarks, "RIGHT_EYE")

    left_elbow = _get_point(landmarks, "LEFT_ELBOW")
    right_elbow = _get_point(landmarks, "RIGHT_ELBOW")

    left_wrist = _get_point(landmarks, "LEFT_WRIST")
    right_wrist = _get_point(landmarks, "RIGHT_WRIST")

    nose = _get_point(landmarks, "NOSE")

    # --- 어깨 관련 메트릭 ---
    if left_shoulder and right_shoulder:
        lx, ly = left_shoulder.get("x"), left_shoulder.get("y")
        rx, ry = right_shoulder.get("x"), right_shoulder.get("y")

        # 값이 제대로 있는지 확인
        if None not in (lx, ly, rx, ry):
            # 1) 어깨 높이 차이 (y좌표 절대값 차이)
            diff = abs(ly - ry)
            metrics["shoulder_height_diff"] = float(diff)

            # 2) 어깨선 기울기 (deg)
            dx = rx - lx
            dy = ry - ly
            metrics["shoulder_line_angle_deg"] = _angle_deg(dx, dy)

    # --- 머리 기울기 (좌/우 귀 기준) ---
    if left_ear and right_ear:
        lx, ly = left_ear.get("x"), left_ear.get("y")
        rx, ry = right_ear.get("x"), right_ear.get("y")

        if None not in (lx, ly, rx, ry):
            dx = rx - lx
            dy = ry - ly
            metrics["head_line_angle_deg"] = _angle_deg(dx, dy)

    # --- 얼굴 크기 (눈 사이 거리) ---
    if left_eye and right_eye:
        lx, ly = left_eye.get("x"), left_eye.get("y")
        rx, ry = right_eye.get("x"), right_eye.get("y")
        if None not in (lx, ly, rx, ry):
            dx = rx - lx
            dy = ry - ly
            face_scale = math.sqrt(dx * dx + dy * dy)
            metrics["face_scale_raw"] = float(face_scale)

    # --- forward head (어깨 대비 귀의 z 차이) ---
    # z가 작을수록(더 음수) 카메라에 가까운 방향이라고 가정
    def _z(name: str) -> Optional[float]:
        p = landmarks.get(name)
        if not isinstance(p, dict):
            return None
        z = p.get("z")
        return float(z) if z is not None else None

    fwd_candidates = []

    # 왼쪽 기준
    if left_shoulder and left_ear:
        sz = _z("LEFT_SHOULDER")
        ez = _z("LEFT_EAR")
        if sz is not None and ez is not None:
            # z는 카메라 쪽이 더 음수이므로,
            # (귀 z - 어깨 z)는 거북목일 때 음수가 됨.
            dz = ez - sz            # 음수이면 머리가 앞으로 나온 상태
            amount = max(-dz, 0.0)  # 앞으로 나온 "양"을 양수로 변환
            fwd_candidates.append(amount)

    # 오른쪽 기준
    if right_shoulder and right_ear:
        sz = _z("RIGHT_SHOULDER")
        ez = _z("RIGHT_EAR")
        if sz is not None and ez is not None:
            dz = ez - sz
            amount = max(-dz, 0.0)
            fwd_candidates.append(amount)

    if fwd_candidates:
        # 양수가 클수록 거북목 정도가 심한 것
        metrics["forward_head_amount"] = float(max(fwd_candidates))

    # --- 팔꿈치/손목 높이 차이 (기대기/팔 괴기 탐지용 보조 신호) ---
    if left_elbow and right_elbow:
        ley = left_elbow.get("y")
        rey = right_elbow.get("y")
        if None not in (ley, rey):
            metrics["elbow_height_diff"] = float(abs(ley - rey))

    if left_wrist and right_wrist:
        lwy = left_wrist.get("y")
        rwy = right_wrist.get("y")
        if None not in (lwy, rwy):
            metrics["wrist_height_diff"] = float(abs(lwy - rwy))

    # --- 손이 얼굴에 얼마나 가까운지 (팔 지지 자세 감지용) ---
    # 우선순위: Hands 결과(LEFT_HAND_WRIST/RIGHT_HAND_WRIST) > Pose 결과(LEFT_WRIST/RIGHT_WRIST)
    hand_left = _get_point(landmarks, "LEFT_HAND_WRIST") or _get_point(landmarks, "LEFT_WRIST")
    hand_right = _get_point(landmarks, "RIGHT_HAND_WRIST") or _get_point(landmarks, "RIGHT_WRIST")
    
    if nose:
        nx, ny = nose.get("x"), nose.get("y")

        if None not in (nx, ny):
            # 왼쪽 손
            if hand_left:
                lx, ly = hand_left.get("x"), hand_left.get("y")
                if None not in (lx, ly):
                    dx = lx - nx
                    dy = ly - ny
                    dist = math.sqrt(dx * dx + dy * dy)
                    metrics["hand_face_dist_left"] = float(dist)

            # 오른쪽 손
            if hand_right:
                rx, ry = hand_right.get("x"), hand_right.get("y")
                if None not in (rx, ry):
                    dx = rx - nx
                    dy = ry - ny
                    dist = math.sqrt(dx * dx + dy * dy)
                    metrics["hand_face_dist_right"] = float(dist)

    return metrics