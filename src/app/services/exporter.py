from typing import Any, Dict


def publish_to_backend(payload: Dict[str, Any]) -> None:
    """
    분석 결과를 Spring Boot 백엔드로 내보내는 자리.
    2단계에서는 네 눈으로 확인만 할 수 있게 print만 한다.
    """
    # TODO: 추후 httpx/requests로 BE에 POST
    print("[EXPORTER] would send payload:", payload)
