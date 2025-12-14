import os
import logging
from datetime import datetime
from typing import Any, Dict, List

import requests
from app.core.config import settings

logger = logging.getLogger(__name__)

def _build_log_url() -> str:
    base = settings.spring_base_url.rstrip("/")
    path = settings.spring_ai_log_path
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"

def _build_headers() -> Dict[str, str]:
    token = os.getenv("SPRING_BEARER_TOKEN", "").strip()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

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

def publish_to_backend(*, session_id: int, result: Dict[str, Any], timeout_sec: float = 0.5) -> None:
    posture_states = _select_posture_status(result)
    now_iso = datetime.now().replace(microsecond=0).isoformat()

    payload: Dict[str, Any] = {
        "sessionId": int(session_id),
        "postureStates": posture_states,
        "timestamp": now_iso,
    }

    url = _build_log_url()
    headers = _build_headers()

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout_sec)
    except requests.RequestException as exc:
        logger.warning("Failed to send posture log to %s: %s", url, exc)
        return

    if resp.status_code not in (200, 202):
        logger.warning("Unexpected status from %s: %s %s", url, resp.status_code, (resp.text or "")[:200])