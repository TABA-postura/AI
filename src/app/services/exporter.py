import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Spring Boot 서버 주소
LOG_URL = f"{settings.spring_base_url.rstrip('/')}{settings.spring_ai_log_path}"

def _build_landmark_payload(result: Dict[str, Any]) -> Optional[str]:
    """
    DB에 TEXT로 넣을 landmarkData 문자열을 만든다.
    너무 크지 않은 선에서, 나중에 디버깅/재학습에 쓸 만한 정보 위주로 담자.
    """
    payload = {
        "state": result.get("state"),
        "violations": result.get("violations"),
        "metrics": result.get("metrics"),
        "landmarks": result.get("landmarks"),
    }

    try:
        return json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.warning("Failed to serialize landmarkData: %s", exc)
        return None

def publish_to_backend(
    *,
    user_id: int,
    session_id: int,
    result: Dict[str, Any],
) -> None:
    """
    Spring Boot의 /ai/log 엔드포인트로 자세 로그를 전송한다.

    - PostureLogRequest DTO 규격에 맞게 JSON을 구성해야 함.
      (userId, sessionId, postureStatus, timestamp, landmarkData)
    """
    # 1) 어떤 자세 상태를 보낼지 결정
    violations = result.get("violations") or []
    if violations:
        # 가장 우선순위 높은 첫 번째 위반 코드를 postureStatus로 사용
        posture_status = violations[0]
    else:
        # 위반이 없으면 GOOD으로 통일
        posture_status = "GOOD"

    # 2) 타임스탬프 (ISO8601, UTC 기준)
    now_iso = datetime.now(timezone.utc).isoformat()

    # 3) landmarkData: JSON 문자열 (또는 None)
    landmark_str = _build_landmark_payload(result)

    payload: Dict[str, Any] = {
        "userId": user_id,
        "sessionId": session_id,
        # 백엔드 DTO 필드명은 postureStatus 임
        "postureStatus": posture_status,
        "timestamp": now_iso,
        "landmarkData": landmark_str,
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