from typing import Dict


def update_baseline(metrics: Dict[str, float]) -> None:
    """
    세션 초반 메트릭으로 개인 기준선을 업데이트하는 자리.
    2단계에서는 실제로 아무것도 하지 않는다.
    """
    # TODO: baseline 저장 로직
    return None


def apply_baseline(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    기준선 대비 편차를 계산해 보정하는 자리.
    지금은 입력을 그대로 반환한다.
    """
    # TODO: baseline 보정 적용
    return metrics
