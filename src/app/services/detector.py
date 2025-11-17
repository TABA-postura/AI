from typing import Any, Dict

import cv2
import numpy as np
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

# 프로세스 전체에서 재사용할 Pose 인스턴스
_pose = mp_pose.Pose(
    static_image_mode=True, # 이미지 한 장씩 분석
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence = 0.5,
)

# Hands 인스턴스 (손 전용)
_hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
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
    이미지 바이트를 받아 MediaPipe Pose + Hands로 랜드마크를 추출한다.

    반환 형식:
    {
        "image_width": int,
        "image_height": int,
        "landmarks": {
            "LEFT_SHOULDER": {...},
            "RIGHT_SHOULDER": {...},
            ...
            "LEFT_HAND_WRIST": {...},
            "RIGHT_HAND_WRIST": {...},
        }
    }
    """
    img_bgr = _decode_image(image_bytes)
    h, w, _ = img_bgr.shape

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 1) 포즈 추출
    pose_results = _pose.process(img_rgb)

    landmarks: Dict[str, Dict[str, float]] = {}

    if pose_results.pose_landmarks:
        for idx, lm in enumerate(pose_results.pose_landmarks.landmark):
            name = mp_pose.PoseLandmark(idx).name  # 예: "LEFT_SHOULDER"
            landmarks[name] = {
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "visibility": lm.visibility,
            }

    # 2) 손 추출
    hands_results = _hands.process(img_rgb)

    if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
        for hand_lms, handedness in zip(
            hands_results.multi_hand_landmarks,
            hands_results.multi_handedness,
        ):
            label = handedness.classification[0].label  # "Left" or "Right"

            if label == "Left":
                key = "LEFT_HAND_WRIST"
            else:
                key = "RIGHT_HAND_WRIST"

            wrist = hand_lms.landmark[mp_hands.HandLandmark.WRIST]
            # Pose와 동일하게 x,y,z는 0~1 정규화 좌표
            landmarks[key] = {
                "x": wrist.x,
                "y": wrist.y,
                "z": wrist.z,
                "visibility": 1.0,
            }

    return {
        "image_width": w,
        "image_height": h,
        "landmarks": landmarks,
    }
