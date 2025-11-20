import json
import logging
import sys
from typing import Any, Dict, List, Optional

from .config import settings


class JsonFormatter(logging.Formatter):
    """
    모든 로그를 JSON 한 줄로 찍는 포맷터.
    extra에 넣은 필드(request_id, user_id, state 등)를 같이 출력한다.
    """

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # extra 필드들 붙이기
        for key in (
            "request_id",
            "user_id",
            "session_id",
            "state",
            "violations",
            "max_confidence",
        ):
            if hasattr(record, key):
                base[key] = getattr(record, key)

        return json.dumps(base, ensure_ascii=False)


def setup_logging() -> None:
    """
    루트 로거에 JSON 포맷 핸들러를 단다.
    """
    root = logging.getLogger()
    if root.handlers:
        # 이미 설정돼 있으면 두 번 세팅하지 않음
        return

    root.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root.handlers.clear()
    root.addHandler(handler)


_inference_logger = logging.getLogger("postura.inference")


def log_inference(
    *,
    user_id: Optional[int],
    session_id: Optional[int],
    state: str,
    violations: List[str],
    violation_details: List[Dict[str, Any]],
) -> None:
    """
    한 번의 /analyze 호출 결과를 로그로 남긴다.
    - user_id, session_id, state, violations, max_confidence 등을 포함.
    """
    max_conf = 0.0
    for v in violation_details:
        c = v.get("confidence")
        if isinstance(c, (float, int)):
            max_conf = max(max_conf, float(c))

    _inference_logger.info(
        "posture_inference",
        extra={
            "user_id": user_id,
            "session_id": session_id,
            "state": state,
            "violations": violations,
            "max_confidence": max_conf,
        },
    )
