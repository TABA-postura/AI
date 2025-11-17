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

    # 어깨 포인트 가져오기
    left_shoulder = _get_point(landmarks, "LEFT_SHOULDER")
    right_shoulder = _get_point(landmarks, "RIGHT_SHOULDER")

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

            # 둘 다 0이면 각도 계산 의미 없음 → 그냥 0도 취급
            if dx == 0 and dy == 0:
                angle_deg = 0.0
            else:
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)

                # 180도(← 방향 수평)도 사실 "기울기는 0도"로 봐야 함
                if angle_deg > 90:
                    angle_deg -= 180
                elif angle_deg < -90:
                    angle_deg += 180

            metrics["shoulder_line_angle_deg"] = float(angle_deg)

    # --- 머리 기울기 (좌/우 귀 기준) ---
    left_ear = _get_point(landmarks, "LEFT_EAR")
    right_ear = _get_point(landmarks, "RIGHT_EAR")

    if left_ear and right_ear:
        lx, ly = left_ear.get("x"), left_ear.get("y")
        rx, ry = right_ear.get("x"), right_ear.get("y")

        if None not in (lx, ly, rx, ry):
            dx = rx - lx
            dy = ry - ly
            metrics["head_line_angle_deg"] = _angle_deg(dx, dy)

    # --- 얼굴 크기 (눈 사이 거리) ---
    left_eye = _get_point(landmarks, "LEFT_EYE")
    right_eye = _get_point(landmarks, "RIGHT_EYE")

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
    if left_shoulder and left_ear:
        sz = _z("LEFT_SHOULDER")
        ez = _z("LEFT_EAR")
        if sz is not None and ez is not None:
            fwd_candidates.append(sz - ez)  # 양수일수록 머리가 앞으로

    if right_shoulder and right_ear:
        sz = _z("RIGHT_SHOULDER")
        ez = _z("RIGHT_EAR")
        if sz is not None and ez is not None:
            fwd_candidates.append(sz - ez)

    if fwd_candidates:
        # 음수는 뒤로 간 것으로 취급하고, 0 이상만 남김
        value = max(max(fwd_candidates), 0.0)
        metrics["forward_head_z_diff"] = float(value)

    # --- 팔꿈치/손목 높이 차이 (기대기/팔 괴기 탐지용 보조 신호) ---
    left_elbow = _get_point(landmarks, "LEFT_ELBOW")
    right_elbow = _get_point(landmarks, "RIGHT_ELBOW")
    left_wrist = _get_point(landmarks, "LEFT_WRIST")
    right_wrist = _get_point(landmarks, "RIGHT_WRIST")

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

    return metrics