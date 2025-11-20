from typing import Any, Dict, List
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
    exporter,
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


def run(
    image_bytes: bytes,
    user_id: int | None = None,
    session_id: int | None = None,
) -> Dict[str, Any]:

    # 현재 시각(ms) - 나중에 should_process 등에서 쓸 수 있음
    now_ms = int(time.time() * 1000)

    # 1) 포즈 랜드마크 추출
    posture_data = detector.detect(image_bytes)

    # (실시간 스트림 연동 시)
    # if not tracker.should_process(now_ms):
    #     이전 결과를 재사용하거나 바로 반환하는 로직을 넣을 수 있음.

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

    # JSON 로그로 남기기
    log_inference(
        user_id=user_id,
        session_id=session_id,
        state=response["state"],
        violations=response["violations"],
        violation_details=violation_details,
    )

    # 백엔드 로그 전송 (user_id, session_id가 있을 때만)
    if user_id is not None and session_id is not None:
        try:
            exporter.publish_to_backend(
                user_id=user_id,
                session_id=session_id,
                result=response,
            )
        except Exception as exc:  # 방어용
            logger.warning("Failed to export posture log: %s", exc)

    # TODO: exporter.publish_to_backend(response)
    return response
