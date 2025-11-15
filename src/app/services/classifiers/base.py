from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ClassificationResult:
    """
    개별 분류기의 결과.
    """
    code: str            # 예: "FORWARD_HEAD"
    is_violation: bool   # 위반 여부
    confidence: float    # 0.0 ~ 1.0 사이 신뢰도


def ok(code: str) -> ClassificationResult:
    """
    '위반 아님' 기본 결과 헬퍼.
    """
    return ClassificationResult(code=code, is_violation=False, confidence=0.0)
