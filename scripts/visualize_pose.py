from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def visualize(input_path: str, output_path: str = "pose_debug.png") -> None:
    img_path = Path(input_path)
    print("[DEBUG] img_path:", img_path, "exists:", img_path.exists())

    if not img_path.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {img_path}")

    # 한글/원드라이브 경로 문제 피하려고 imdecode 사용
    data = img_path.read_bytes()
    file_bytes = np.frombuffer(data, np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise ValueError(f"이미지 로드에 실패했습니다: {img_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Pose + Hands 둘 다 사용
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    ) as pose, mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        pose_results = pose.process(img_rgb)
        hands_results = hands.process(img_rgb)

        # 1) Pose 랜드마크 + 스켈레톤 그리기
        if pose_results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image=img_bgr,
                landmark_list=pose_results.pose_landmarks,
                connections=mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
            )

        # 2) Hands 랜드마크 + 연결선 그리기
        if hands_results.multi_hand_landmarks:
            print(f"[DEBUG] detected hands: {len(hands_results.multi_hand_landmarks)}")
            for hand_lms in hands_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image=img_bgr,
                    landmark_list=hand_lms,
                    connections=mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=mp_styles.get_default_hand_landmarks_style(),
                    connection_drawing_spec=mp_styles.get_default_hand_connections_style(),
                )

    cv2.imwrite(output_path, img_bgr)
    print(f"결과 저장됨: {output_path}")


if __name__ == "__main__":
    # 프로젝트 루트 기준 경로
    test_image = r"C:\Users\USER\Documents\posture_test\pose1.jpg"
    visualize(test_image, "pose_debug.png")