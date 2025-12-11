import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Spring Boot 서버 주소
LOG_URL = f"http://13.239.176.67:8080"

def _build_landmark_payload(result: Dict[str, Any]) -> Optional[str]:
    """
    DB에 TEXT로 넣을 landmarkData 문자열을 만듦
    """
    detail_payload = {
        "state": result.get("state"),
        "violations": result.get("violations") or [],
    }

    try:
        return json.dumps(detail_payload, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.warning("Failed to serialize landmarkData: %s", exc)
        return None

def _select_posture_status(result: Dict[str, Any]) -> str:
    """
    AI 내부 결과(state/violations)를 BE에서 요구하는 postureStatus 하나로 매핑.

    - violations가 있으면: 가장 우선순위 높은 코드(violations[0])
    - violations가 없고 state != GOOD 이면: UNKNOWN / ERROR 그대로 사용
    - 나머지: GOOD
    """
    state = result.get("state")
    violations = result.get("violations") or []

    # 1) 위반 자세가 하나 이상 있으면 → 다 보냄
    if violations:
        # 혹시 모를 타입 방어용으로 str() 한번 감싸줌
        return [str(v) for v in violations]

    # 2) 위반이 없을 때 → 메타 state 기준으로 단일 코드
    if state == "GOOD":
        return ["GOOD"]
    if state == "UNKNOWN":
        return ["UNKNOWN"]

    # 3) ERROR 등 기타 상태는 일단 UNKNOWN으로 통일 (BE에서 별도 처리 원하면 여기 수정)
    return ["UNKNOWN"]

def publish_to_backend(
    *,
    session_id: int,
    result: Dict[str, Any],
) -> None:
    # 1) postureStatus 결정
    posture_status = _select_posture_status(result)

    # 2) 타임스탬프 (초까지만) - BE는 LocalDateTime(예: 2025-11-17T13:30:00) 형태 기대
    now_iso = datetime.now().replace(microsecond=0).isoformat()

    # 3) (선택) landmarkData 만들기
    landmark_data = _build_landmark_payload(result)

    # 4) 최종 Payload 구성
    payload: Dict[str, Any] = {
        "sessionId": session_id,
        "postureStatus": posture_status,
        "timestamp": now_iso,
    }

    # BE DTO에 landmarkData 필드가 있다면, 아래 줄을 살려서 같이 보내도 됨
    if landmark_data is not None:
        payload["landmarkData"] = landmark_data

    try:
        resp = requests.post(LOG_URL, json=payload, timeout=0.5)
    except requests.RequestException as exc:
        # 백엔드가 죽어 있더라도 AI 분석은 계속 돌아가야 하므로 예외 삼킴
        logger.warning("Failed to send posture log to %s: %s", LOG_URL, exc)
        return

    if resp.status_code != 202:
        logger.warning(
            "Unexpected status from /ai/log: %s %s",
            resp.status_code,
            resp.text[:200],
        )