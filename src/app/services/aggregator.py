from typing import Any, Dict, List

from .classifiers.base import ClassificationResult


def aggregate(results: List[ClassificationResult]) -> Dict[str, Any]:
    """
    여러 분류기 결과를 종합해 최종 상태를 만든다.
    2단계에서는 is_violation=True가 있는지 여부만 대충 본다.
    (실제 임계값/우선순위 로직은 이후 단계에서 추가)
    """
    violations = [r for r in results if r.is_violation]

    if not violations:
        state = "GOOD"
    else:
        state = "WARN"

    return {
        "state": state,
        "violations": [v.code for v in violations],
    }
