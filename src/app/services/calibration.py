from typing import Dict

# baseline 상태 (메트릭별 평균값)
_baseline: Dict[str, float] = {}
_sample_count: int = 0

# 세션 초반 N프레임 정도만 baseline으로 사용
_MAX_SAMPLES = 30

def update_baseline(metrics: Dict[str, float]) -> None:
    """
    세션 초반 N프레임 동안 여러 메트릭을 모아서 baseline으로 사용한다.

    - face_scale_raw: 화면과의 거리(얼굴 크기)
    - forward_head_amount: 어깨 대비 머리가 앞으로 나온 정도
    - shoulder_height_diff: 양 어깨 y좌표 차이
    - shoulder_line_angle_deg: 어깨선 기울기 (deg)
    - head_line_angle_deg: 머리 기울기 (deg)

    baseline에는 각 값의 '평균값'을 저장한다.
    """
    global _baseline, _sample_count

    if not metrics:
        return

    if _sample_count >= _MAX_SAMPLES:
        return

    # baseline 후보가 되는 원시 메트릭들
    # (각각 metrics.compute()에서 계산됨)
    face_scale = metrics.get("face_scale_raw")
    fwd_head = metrics.get("forward_head_amount")
    sh_diff = metrics.get("shoulder_height_diff")
    sh_angle = metrics.get("shoulder_line_angle_deg")
    head_angle = metrics.get("head_line_angle_deg")

    # 이 중 하나라도 있으면 baseline 업데이트 대상이 있다고 봄
    if all(v is None for v in [face_scale, fwd_head, sh_diff, sh_angle, head_angle]):
        return

    _sample_count += 1

    # 첫 샘플이라면 현재 값을 그대로 baseline으로 사용
    if not _baseline:
        if face_scale is not None:
            _baseline["face_scale_raw"] = float(face_scale)
        if fwd_head is not None:
            _baseline["forward_head_amount"] = float(fwd_head)
        if sh_diff is not None:
            _baseline["shoulder_height_diff"] = float(sh_diff)
        if sh_angle is not None:
            # 기울기는 부호와 상관없이 절대값으로 baseline 저장
            _baseline["shoulder_tilt_abs_deg"] = float(abs(sh_angle))
        if head_angle is not None:
            _baseline["head_tilt_abs_deg"] = float(abs(head_angle))
        return

    # 이후부터는 running mean (증분 평균)으로 baseline 업데이트
    def _update_mean(key: str, new_value: float) -> None:
        prev = _baseline.get(key, new_value)
        # 모든 메트릭이 공통으로 _sample_count를 쓰는 구조
        updated = prev + (new_value - prev) / float(_sample_count)
        _baseline[key] = updated

    if face_scale is not None:
        _update_mean("face_scale_raw", float(face_scale))

    if fwd_head is not None:
        _update_mean("forward_head_amount", float(fwd_head))

    if sh_diff is not None:
        _update_mean("shoulder_height_diff", float(sh_diff))

    if sh_angle is not None:
        _update_mean("shoulder_tilt_abs_deg", float(abs(sh_angle)))

    if head_angle is not None:
        _update_mean("head_tilt_abs_deg", float(abs(head_angle)))


def apply_baseline(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    baseline 대비 변화량으로 delta 메트릭들을 계산해 추가한다.

    - face_scale_raw      → face_scale_delta
    - forward_head_amount → forward_head_delta
    - shoulder_height_diff → shoulder_height_delta
    - shoulder_line_angle_deg → shoulder_tilt_delta (절대각 기준)
    - head_line_angle_deg → head_tilt_delta (절대각 기준)

    baseline이 아직 준비되지 않은 경우에는 원본 metrics를 그대로 반환한다.
    """
    if not _baseline:
        return metrics

    adjusted = dict(metrics)

    # 1) 화면과의 거리 (얼굴 크기)
    base_face = _baseline.get("face_scale_raw")
    cur_face = metrics.get("face_scale_raw")
    if base_face is not None and cur_face is not None:
        adjusted["face_scale_delta"] = float(cur_face) - float(base_face)

    # 2) 거북목 (어깨 대비 머리 앞으로 나온 정도)
    base_fh = _baseline.get("forward_head_amount")
    cur_fh = metrics.get("forward_head_amount")
    if base_fh is not None and cur_fh is not None:
        delta = float(cur_fh) - float(base_fh)
        # baseline보다 뒤로 간 경우(음수)는 0으로 잘라서 '앞으로 나간 정도'만 남김
        adjusted["forward_head_delta"] = max(0.0, delta)

    # 3) 어깨 높이 차이
    base_sh_diff = _baseline.get("shoulder_height_diff")
    cur_sh_diff = metrics.get("shoulder_height_diff")
    if base_sh_diff is not None and cur_sh_diff is not None:
        delta = float(cur_sh_diff) - float(base_sh_diff)
        adjusted["shoulder_height_delta"] = max(0.0, delta)

    # 4) 어깨선 기울기 (deg)
    base_sh_tilt = _baseline.get("shoulder_tilt_abs_deg")
    cur_sh_angle = metrics.get("shoulder_line_angle_deg")
    if base_sh_tilt is not None and cur_sh_angle is not None:
        cur_tilt = abs(float(cur_sh_angle))
        delta = cur_tilt - float(base_sh_tilt)
        adjusted["shoulder_tilt_delta"] = max(0.0, delta)

    # 5) 머리 기울기 (deg)
    base_head_tilt = _baseline.get("head_tilt_abs_deg")
    cur_head_angle = metrics.get("head_line_angle_deg")
    if base_head_tilt is not None and cur_head_angle is not None:
        cur_tilt = abs(float(cur_head_angle))
        delta = cur_tilt - float(base_head_tilt)
        adjusted["head_tilt_delta"] = max(0.0, delta)

    return adjusted

def reset() -> None:
    """
    baseline 초기화 (세션 재시작 / 화면 재설정 등에 사용).
    """
    global _baseline, _sample_count
    _baseline = {}
    _sample_count = 0