from pathlib import Path

import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def visualize(input_path: str, output_path: str = "pose_debug.png") -> None:
    img_path = Path(input_path)
    if not img_path.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {img_path}")

    img_bgr = cv2.imread(str(img_path))
    if img_bgr is None:
        raise ValueError("이미지 로드에 실패했습니다.")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    ) as pose:
        results = pose.process(img_rgb)

        if not results.pose_landmarks:
            print("사람 포즈를 찾지 못했습니다.")
        else:
            # 랜드마크 + 스켈레톤 그리기
            mp_drawing.draw_landmarks(
                image=img_bgr,
                landmark_list=results.pose_landmarks,
                connections=mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style(),
            )

    cv2.imwrite(output_path, img_bgr)
    print(f"결과 저장됨: {output_path}")


if __name__ == "__main__":
    # 테스트용 이미지 경로
    test_image = r"C:\Users\USER\Documents\posture_test\pose1.jpg"
    visualize(test_image, "pose_debug.png")
