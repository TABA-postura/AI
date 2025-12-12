from typing import Any, Optional, Dict, List
import time
import logging

from app.core.logging import log_inference

from . import (
    detector,
    metrics as metrics_mod,
    tracker,
    calibration,
    aggregator,
    advisor,
)

logger = logging.getLogger(__name__)

from .classifiers import (
    uneven_shoulders,
    upper_body_tilt,
    head_tilt,
    too_close,
    leaning_on_arm,
    asymmetric_posture,
    forward_head,
)
from .classifiers.base import ClassificationResult

# 필수 포인트가 없는 경우
REQUIRED_KEYS = ["LEFT_SHOULDER", "RIGHT_SHOULDER", "NOSE"]

def _is_frame_reliable(posture_data: Dict[str, Any]) -> bool:
    landmarks = posture_data.get("landmarks") or {}
    if not isinstance(landmarks, dict):
        return False

    if not landmarks:
        return False

    # 필수 포인트 중 최소 2개 이상은 있어야 “신뢰 가능”으로 인정
    hit = 0
    for key in REQUIRED_KEYS:
        if key in landmarks:
            hit += 1
    return hit >= 2

def run(
    image_bytes: bytes,
    *,
    session_id: Optional[int] = None,
    reset: bool = False,
) -> Dict[str, Any]:

    # 현재 시각(ms)
    now_ms = int(time.time() * 1000)

    # 0) 포즈 랜드마크 추출
    posture_data = detector.detect(image_bytes)

    # 1) 좌표 신뢰도 체크
    if not _is_frame_reliable(posture_data):
        # 이 프레임은 'UNKNOWN' 상태로 처리
        response: Dict[str, Any] = {
            "state": "UNKNOWN",
            "violations": [],
            "violation_details": [],
            "advices": [
                {
                    "code": "UNKNOWN",
                    "message": "사용자 자세를 인식할 수 없었습니다. 카메라 안에 상반신이 잘 보이도록 위치를 조정해 주세요.",
                    "content_id": None,
                }
            ],
            "metrics": {},
            "timestamp_ms": now_ms,
        }

        # UNKNOWN도 로그/BE전송이 필요하면 여기서 처리하고 return
        log_inference(
            user_id=None,
            session_id=session_id,
            state=response["state"],
            violations=[],
            violation_details=[],
        )

        return response

    # 2) 트래킹/스무딩
    smoothed = tracker.smooth_landmarks(posture_data)

    # 3) 메트릭 계산
    raw_metrics = metrics_mod.compute(smoothed)

    # 4) baseline 업데이트 + 보정 적용
    calibration.update_baseline(raw_metrics)
    calibrated_metrics = calibration.apply_baseline(raw_metrics)

    # 5) 분류기들 실행
    results: List[ClassificationResult] = [
        uneven_shoulders.classify(calibrated_metrics),
        upper_body_tilt.classify(calibrated_metrics),
        head_tilt.classify(calibrated_metrics),
        too_close.classify(calibrated_metrics),
        leaning_on_arm.classify(calibrated_metrics),
        asymmetric_posture.classify(calibrated_metrics),
        forward_head.classify(calibrated_metrics),
    ]

    # 6) 최종 상태 집계 + 코칭 문구 생성
    aggregate_result = aggregator.aggregate(results)
    advices = advisor.advise(aggregate_result)

    violation_details = aggregate_result.get("violation_details", [])

    response: Dict[str, Any] = {
        "state": aggregate_result.get("state", "GOOD"),
        "violations": aggregate_result.get("violations", []),
        "violation_details": violation_details,
        "advices": advices,
        "metrics": calibrated_metrics,  # 디버깅 용
        "timestamp_ms": now_ms, # 현재 시각
    }

    return response
