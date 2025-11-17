from typing import Dict

# baseline 상태 (메트릭별 평균값)
_baseline: Dict[str, float] = {}
_sample_count: int = 0

# 세션 초반 N프레임 정도만 baseline으로 사용
_MAX_SAMPLES = 30

def update_baseline(metrics: Dict[str, float]) -> None:
    """
    세션 초반 N프레임 동안 메트릭의 평균을 구해 baseline으로 사용한다.
    - 어깨/머리 같은 메트릭도 넣어둘 수 있지만,
      실제로는 face_scale, distance 계열 메트릭에 더 유용하다.

    """
    global _baseline, _sample_count

    if not metrics:
        return

    # baseline을 어느 정도 모으면 더 이상 업데이트하지 않음
    if _sample_count >= _MAX_SAMPLES:
        return

    _sample_count += 1

    if not _baseline:
        # 첫 샘플이면 그대로 복사
        _baseline = dict(metrics)
        return

    # running mean (증분 평균)
    for key, value in metrics.items():
        prev = _baseline.get(key, value)
        new_val = prev + (value - prev) / float(_sample_count)
        _baseline[key] = new_val


def apply_baseline(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    baseline 대비 변화량으로 보정할 메트릭에만 baseline을 적용한다.

    현재 단계에서는 face_scale 등 개인차가 큰 메트릭 위주로 사용하고,
    어깨 관련 메트릭(shoulder_height_diff / shoulder_line_angle_deg)은
    그대로 사용하는 것이 더 자연스러워서 보정하지 않는다.
    """
    if not _baseline:
        return metrics

    adjusted = dict(metrics)

    # 나중에 추가할 '개인차 큰 메트릭' 리스트 (예: 화면과의 거리)
    CALIBRATED_KEYS = {"face_scale"}

    for key in CALIBRATED_KEYS:
        if key in adjusted and key in _baseline:
            adjusted[key] = adjusted[key] - _baseline[key]

    return adjusted

def reset() -> None:
    """
    baseline 초기화 (세션 재시작 / 화면 재설정 등에 사용).
    """
    global _baseline, _sample_count
    _baseline = {}
    _sample_count = 0
