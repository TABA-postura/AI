from typing import Any, Dict

import cv2
import numpy as np
import mediapipe as mp

mp_pose = mp.solutions.pose

# 프로세스 전체에서 재사용할 Pose 인스턴스
_pose = mp_pose.Pose(
    static_image_mode=True, # 이미지 한 장씩 분석
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence = 0.5,
)

def _decode_image(image_bytes: bytes) -> np.ndarray:
    """
    바이트 -> OpenCV BGR 이미지로 디코드.
    """
    file_bytes = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("이미지 디코딩에 실패했습니다.")
    return img_bgr

def detect(image_bytes: bytes) -> Dict[str, Any]:
    """
    이미지 바이트를 받아 MediaPipe Pose로 랜드마크를 추출한다.

    반환 형식:
    {
        "image_width": int,
        "image_height": int,
        "landmarks": {
            "LEFT_SHOULDER": {"x": float, "y": float, "z": float, "visibility": float},
            ...
        }
    }
    """
    img_bgr = _decode_image(image_bytes)
    h, w, _ = img_bgr.shape

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = _pose.process(img_rgb)

    if not results.pose_landmarks:
        # 사람 못 찾았을 때
        return {
            "image_width": w,
            "image_height": h,
            "landmarks": {},
        }

    landmarks: Dict[str, Dict[str, float]] = {}
    for idx, lm in enumerate(results.pose_landmarks.landmark):
        # mp_pose.PoseLandmark(idx) -> Enum, .name 하면 "LEFT_SHOULDER" 이런 문자열 됨
        name = mp_pose.PoseLandmark(idx).name
        landmarks[name] = {
            "x": lm.x,            # 0~1, 이미지 너비 기준 정규화
            "y": lm.y,            # 0~1, 이미지 높이 기준 정규화 (위=0, 아래=1)
            "z": lm.z,            # 대략적인 깊이
            "visibility": lm.visibility,
        }

    return {
        "image_width": w,
        "image_height": h,
        "landmarks": landmarks,
    }
