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

def compute(posture_data: Dict[str, Any]) -> Dict[str, float]:
    """
    자세 데이터(posture_data)에서 숫자 메트릭들을 계산한다.

    반환 예:
    {
        "shoulder_height_diff": 0.04,
        "shoulder_line_angle_deg": 7.2
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

            # 둘 다 0이면 각도 계산 의미 없음 → 그냥 0도 취급
            if dx == 0 and dy == 0:
                angle_deg = 0.0
            else:
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)

            metrics["shoulder_line_angle_deg"] = float(angle_deg)

    # 앞으로 head, too_close 등 메트릭도 여기서 계속 추가할 예정
    return metrics
