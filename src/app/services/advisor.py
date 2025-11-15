from typing import Any, Dict, List


def advise(aggregate_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    최종 상태를 기반으로 사용자에게 보여줄 코칭 메시지 리스트를 만든다.
    2단계에서는 심플한 더미 메시지만 반환한다.
    """
    state = aggregate_result.get("state", "UNKNOWN")

    if state == "GOOD":
        return [
            {
                "code": "GOOD",
                "message": "좋은 자세를 유지하고 있어요! 👏",
            }
        ]

    if state == "WARN":
        return [
            {
                "code": "GENERIC_WARN",
                "message": "자세 분석 기능이 준비 중입니다. 곧 더 정확한 피드백을 드릴게요.",
            }
        ]

    return [
        {
            "code": "UNKNOWN",
            "message": "자세 상태를 판단할 수 없습니다.",
        }
    ]
