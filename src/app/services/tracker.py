from typing import Any, Dict


def should_process(timestamp_ms: int) -> bool:
    """
    이 프레임을 처리할지 말지 결정하는 로직 자리.
    2단계에서는 무조건 True를 반환한다.
    """
    # TODO: 타깃 FPS에 맞춘 다운샘플링 로직
    return True


def smooth_landmarks(landmarks: Dict[str, Any]) -> Dict[str, Any]:
    """
    랜드마크를 EMA 등으로 스무딩하는 자리.
    지금은 그대로 되돌려준다.
    """
    # TODO: 스무딩 로직 추가
    return landmarks
