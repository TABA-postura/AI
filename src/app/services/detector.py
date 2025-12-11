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

# 필수 포즈 랜드마크 정의
REQUIRED_KEYS = ["LEFT_SHOULDER", "RIGHT_SHOULDER", "NOSE"]

def _is_frame_reliable(posture_data: Dict[str, Any]) -> bool:
    landmarks = posture_data.get("landmarks") or {}
    if not isinstance(landmarks, dict) or not landmarks:
        # 랜드마크가 없거나 잘못된 형식일 경우
        return False

    # 필수 포인트 중 최소 2개 이상은 있어야 신뢰할 수 있다고 판단
    hit = 0
    for key in REQUIRED_KEYS:
        if key in landmarks:
            hit += 1
    return hit >= 2  # 최소 두 개 이상의 랜드마크가 있어야 신뢰 가능

def detect(image_bytes: bytes) -> Dict[str, Any]:
    """
    이미지 바이트를 받아 MediaPipe Pose + Hands로 랜드마크를 추출한다.
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

    # 손 추출
    hands_results = _hands.process(img_rgb)

    if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
        for hand_lms, handedness in zip(
            hands_results.multi_hand_landmarks,
            hands_results.multi_handedness,
        ):
            label = handedness.classification[0].label  # "Left" or "Right"
            key = f"{label}_HAND_WRIST"
            wrist = hand_lms.landmark[mp_hands.HandLandmark.WRIST]
            landmarks[key] = {
                "x": wrist.x,
                "y": wrist.y,
                "z": wrist.z,
                "visibility": 1.0,
            }

    # 랜드마크 신뢰도 체크
    if not _is_frame_reliable({"landmarks": landmarks}):
        # 신뢰할 수 없는 프레임이라면 UNKNOWN 상태로 처리
        return {
            "image_width": w,
            "image_height": h,
            "landmarks": landmarks,
            "state": "UNKNOWN",  # 상태를 UNKNOWN으로 설정
            "violations": [],  # 위반 사항 없음
            "advices": [{
                "code": "UNKNOWN",
                "message": "사용자 자세를 인식할 수 없었습니다. 카메라 안에 상반신이 잘 보이도록 위치를 조정해 주세요.",
                "content_id": None,
            }],
            "metrics": {},
        }

    # 정상적인 경우에는 랜드마크와 함께 계속 진행
    return {
        "image_width": w,
        "image_height": h,
        "landmarks": landmarks,
        "state": "GOOD",  # 정상 상태
        "violations": [],
        "advices": [],
        "metrics": {},
    }
