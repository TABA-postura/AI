from typing import Dict

# baseline 상태 (메트릭별 평균값)
_baseline: Dict[str, float] = {}
_sample_count: int = 0

# 세션 초반 N프레임 정도만 baseline으로 사용
_MAX_SAMPLES = 30

def update_baseline(metrics: Dict[str, float]) -> None:
    """
    세션 초반 N프레임 동안 face_scale_raw 등을 모아서 baseline으로 사용한다.
    - 지금은 화면과의 거리(얼굴 크기)에만 baseline 적용.

    """
    global _baseline, _sample_count

    if not metrics:
        return

    # baseline에 사용할 key들
    keys = ["face_scale_raw"]
    has_any = any(k in metrics for k in keys)
    if not has_any:
        return
    
    if _sample_count >= _MAX_SAMPLES:
        return

    _sample_count += 1

    if not _baseline:
        # 첫 샘플이면 필요한 key만 복사
        _baseline = {k: metrics[k] for k in keys if k in metrics}
        return

    # running mean (증분 평균)
    for key in keys:
        if key not in metrics:
            continue
        value = metrics[key]
        prev = _baseline.get(key, value)
        new_val = prev + (value - prev) / float(_sample_count)
        _baseline[key] = new_val


def apply_baseline(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    baseline 대비 변화량으로 face_scale_delta를 계산해 추가한다.

    - face_scale_raw: 원래 절대값 (0~1)
    - face_scale_delta: baseline 대비 증가량 (양수면 화면에 더 가까워진 것)
    """
    if not _baseline:
        return metrics

    adjusted = dict(metrics)

    base_face = _baseline.get("face_scale_raw")
    cur_face = metrics.get("face_scale_raw")

    if base_face is not None and cur_face is not None:
        adjusted["face_scale_delta"] = cur_face - base_face

    return adjusted

def reset() -> None:
    """
    baseline 초기화 (세션 재시작 / 화면 재설정 등에 사용).
    """
    global _baseline, _sample_count
    _baseline = {}
    _sample_count = 0
