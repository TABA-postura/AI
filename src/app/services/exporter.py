import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

# Spring Boot 서버 주소
LOG_URL = f"http://13.239.176.67:8080/ai/log"

def _select_posture_status(result: Dict[str, Any]) -> List[str]:
    """
    - state == GOOD    -> ["GOOD"]
    - state == UNKNOWN -> ["UNKNOWN"]
    - state == WARN    -> violations 배열 그대로(단, GOOD/UNKNOWN 등 섞이면 제거)
    - 기타/예외        -> ["UNKNOWN"]
    """
    state = result.get("state")
    violations = result.get("violations") or []

    # WARN이면 violations를 우선 사용
    if state == "WARN":
        cleaned = [str(v) for v in violations if v and v not in ("GOOD", "UNKNOWN", "ERROR", "WARN")]
        return cleaned if cleaned else ["GOOD"]

    # 그 외는 state로 단일 결정
    if state == "GOOD":
        return ["GOOD"]
    if state == "UNKNOWN":
        return ["UNKNOWN"]

    # ERROR 등 기타는 운영 정책에 맞게 처리
    return ["UNKNOWN"]

def publish_to_backend(
    *,
    session_id: int,
    result: Dict[str, Any],
    timeout_sec: float = 0.5,
) -> None:
    
    posture_states = _select_posture_status(result)
    now_iso = datetime.now().replace(microsecond=0).isoformat()

    payload: Dict[str, Any] = {
        "sessionId": int(session_id),
        "postureStates": posture_states,
        "timestamp": now_iso,
    }

    try:
        resp = requests.post(LOG_URL, json=payload, timeout=timeout_sec)
    except requests.RequestException as exc:
        logger.warning("Failed to send posture log to %s: %s", LOG_URL, exc)
        return

    # 202 Accepted :contentReference[oaicite:9]{index=9}
    if resp.status_code not in (200, 202):
        logger.warning(
            "Unexpected status from %s: %s %s",
            LOG_URL,
            resp.status_code,
            (resp.text or "")[:200],
        )