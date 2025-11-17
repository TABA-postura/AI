from typing import Any, Dict, List

from .classifiers.base import ClassificationResult


# 코드별 심각도 (숫자가 클수록 더 중요한 문제)
SEVERITY_RANK = {
    "TOO_CLOSE": 3,
    "FORWARD_HEAD": 3,
    "HEAD_TILT": 2,
    "UNEQUAL_SHOULDERS": 2,
    "UPPER_BODY_TILT": 2,
    "LEANING_ON_ARM": 2,
    "ASYMMETRIC_POSTURE": 1,
}

def aggregate(results: List[ClassificationResult]) -> Dict[str, Any]:
    """
    여러 분류기 결과를 종합해 최종 상태를 만든다.
    - is_violation=True인 것들만 모아서
      severity, confidence 기준으로 정렬한다.
    """
    violations: List[Dict[str, Any]] = []

    for r in results:
        if not r.is_violation:
            continue

        severity = SEVERITY_RANK.get(r.code, 1)
        violations.append(
            {
                "code": r.code,
                "confidence": r.confidence,
                "severity": severity,
            }
        )

    # severity 내림차순, 그다음 confidence 내림차순 정렬
    violations.sort(key=lambda v: (-v["severity"], -v["confidence"]))

    state = "GOOD" if not violations else "WARN"

    return {
        "state": state,
        # 간단한 코드 리스트 (FE/BE용)
        "violations": [v["code"] for v in violations],
        # 상세 정보 (추가 정보 필요시 사용)
        "violation_details": violations,
    }