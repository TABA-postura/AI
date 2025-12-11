import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Spring Boot 서버 주소
LOG_URL = f"{settings.spring_base_url.rstrip('/')}{settings.spring_ai_log_path}"

def _build_landmark_payload(result: Dict[str, Any]) -> Optional[str]:
    """
    DB에 TEXT로 넣을 landmarkData 문자열을 만듦
    """
    detail_payload = {
        "state": result.get("state"),
        "violations": result.get("violations"),
        "metrics": result.get("metrics"),
    }

    try:
        return json.dumps(detail_payload, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.warning("Failed to serialize landmarkData: %s", exc)
        return None

def publish_to_backend(
    *,
    session_id: int,
    result: Dict[str, Any],
) -> None:

    state = result.get("state")
    violations = result.get("violations") or []

    if violations:
        # 가장 우선순위 높은 첫 번째 위반을 그대로 postureStatus로 사용
        posture_status = violations[0]
    elif state and state != "GOOD":
        # 위반은 없지만, GOOD도 아닌 상태 (UNKNOWN, ERROR 등)은 state 자체를 태깅
        posture_status = state
    else:
        posture_status = "GOOD"

    # 2) 타임스탬프 (초까지만)
    now_iso = datetime.now().replace(microsecond=0).isoformat()

    payload: Dict[str, Any] = {
        "sessionId": session_id,
        "postureStatus": posture_status,
        "timestamp": now_iso,
    }

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