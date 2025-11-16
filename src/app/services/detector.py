from typing import Any, Dict


def detect(image_bytes: bytes) -> Dict[str, Any]:
    """
    이미지 바이트를 입력으로 받아 포즈 랜드마크를 추출하는 자리.
    2단계에서는 아직 실제 분석 안 하고 더미 값만 반환한다.
    """
    # TODO: MediaPipe Pose 연동
    return {
        "landmarks": [],
        "image_size": None,
    }
