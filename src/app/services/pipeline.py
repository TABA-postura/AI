from typing import Any, Dict, List

from . import detector, metrics as metrics_mod, tracker, calibration, aggregator, advisor
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


def run(image_bytes: bytes) -> Dict[str, Any]:
    """
    메인 파이프라인: 이미지 -> 랜드마크 -> 메트릭 -> 분류기 -> 최종 상태.
    """
    # 1) 포즈 랜드마크 추출
    posture_data = detector.detect(image_bytes)

    # 2) 트래킹/스무딩 & 캘리브레이션 (지금은 더미)
    smoothed = tracker.smooth_landmarks(posture_data)
    raw_metrics = metrics_mod.compute(smoothed)
    calibrated_metrics = calibration.apply_baseline(raw_metrics)

    # 3) 분류기들 실행
    results: List[ClassificationResult] = [
        uneven_shoulders.classify(calibrated_metrics),
        upper_body_tilt.classify(calibrated_metrics),
        head_tilt.classify(calibrated_metrics),
        too_close.classify(calibrated_metrics),
        leaning_on_arm.classify(calibrated_metrics),
        asymmetric_posture.classify(calibrated_metrics),
        forward_head.classify(calibrated_metrics),
    ]

    # 4) 최종 상태 집계 + 코칭 문구 생성
    aggregate_result = aggregator.aggregate(results)
    advices = advisor.advise(aggregate_result)

    response: Dict[str, Any] = {
        "state": aggregate_result.get("state", "GOOD"),
        "violations": aggregate_result.get("violations", []),
        "advices": advices,
        "metrics": calibrated_metrics,  # 이 줄 있으면 디버깅에 좋음
    }

    return response
