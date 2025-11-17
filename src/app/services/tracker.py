from typing import Any, Dict, Optional

# 타깃 FPS (실시간 스트림에서 쓸 예정)
TARGET_FPS = 3.0
_MIN_INTERVAL_MS = int(1000 / TARGET_FPS)

# 프레임 간 시간 추적용
_last_ts_ms: Optional[int] = None

# 랜드마크 EMA(지수이동평균) 상태
_ema_landmarks: Dict[str, Dict[str, float]] = {}

# EMA 계수 (0~1) - 1에 가까울수록 최신 프레임을 더 많이 반영
ALPHA = 0.4

def should_process(timestamp_ms: int) -> bool:
    """
    이 프레임을 처리할지 말지 결정하는 로직 자리.
    - 실시간 스트리밍 시, 너무 자주 들어오는 프레임은 스킵하려고 사용.
    - 지금 HTTP 단건 분석(/posture/analyze)에서는 아직 사용하지 않아도 됨.
    """
    global _last_ts_ms

    if _last_ts_ms is None:
        _last_ts_ms = timestamp_ms
        return True

    if timestamp_ms - _last_ts_ms < _MIN_INTERVAL_MS:
        # 아직 다음 처리 시점이 안 됨 → 스킵
        return False

    _last_ts_ms = timestamp_ms
    return True


def smooth_landmarks(posture_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    랜드마크 좌표에 간단한 EMA(지수 이동 평균)를 적용해
    프레임 간 흔들림을 줄인다.
    """
    global _ema_landmarks

    landmarks = posture_data.get("landmarks") or {}
    if not isinstance(landmarks, dict) or not landmarks:
        # 스무딩할 데이터가 없으면 그대로 반환
        return posture_data

    smoothed_landmarks: Dict[str, Dict[str, float]] = {}

    for name, point in landmarks.items():
        # 새 관측값
        x = float(point.get("x", 0.0))
        y = float(point.get("y", 0.0))
        z = float(point.get("z", 0.0))
        v = float(point.get("visibility", 0.0))

        prev = _ema_landmarks.get(name)
        if prev is None:
            # 첫 프레임이면 그대로 채택
            new_val = {"x": x, "y": y, "z": z, "visibility": v}
        else:
            # EMA 적용
            new_val = {
                "x": ALPHA * x + (1.0 - ALPHA) * prev["x"],
                "y": ALPHA * y + (1.0 - ALPHA) * prev["y"],
                "z": ALPHA * z + (1.0 - ALPHA) * prev["z"],
                "visibility": ALPHA * v + (1.0 - ALPHA) * prev["visibility"],
            }

        smoothed_landmarks[name] = new_val

    _ema_landmarks = smoothed_landmarks

    # posture_data 복사본에 스무딩된 랜드마크를 넣어서 반환
    new_posture = dict(posture_data)
    new_posture["landmarks"] = smoothed_landmarks
    return new_posture

def reset() -> None:
    """
    트래커 상태 초기화 (FPS/EMA 모두).
    - 사용자가 '화면 재설정' 버튼 눌렀을 때 호출하면 좋음.
    """
    global _last_ts_ms, _ema_landmarks
    _last_ts_ms = None
    _ema_landmarks = {}