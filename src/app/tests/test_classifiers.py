from app.services.classifiers import (
    uneven_shoulders,
    upper_body_tilt,
    forward_head,
    too_close,
    leaning_on_arm,
)


def test_unequal_shoulders_below_threshold():
    metrics = {"shoulder_height_diff": uneven_shoulders.THRESHOLD - 0.01}
    result = uneven_shoulders.classify(metrics)
    assert result.is_violation is False
    assert result.confidence == 0.0


def test_unequal_shoulders_above_threshold():
    value = uneven_shoulders.THRESHOLD + 0.02
    metrics = {"shoulder_height_diff": value}
    result = uneven_shoulders.classify(metrics)
    assert result.is_violation is True
    assert 0.0 <= result.confidence <= 1.0


def test_upper_body_tilt_no_violation():
    metrics = {"shoulder_line_angle_deg": upper_body_tilt.THRESHOLD_DEG - 1}
    result = upper_body_tilt.classify(metrics)
    assert result.is_violation is False


def test_upper_body_tilt_violation():
    metrics = {"shoulder_line_angle_deg": upper_body_tilt.THRESHOLD_DEG + 3}
    result = upper_body_tilt.classify(metrics)
    assert result.is_violation is True


def test_forward_head_no_violation():
    metrics = {"forward_head_amount": forward_head.THRESHOLD - 0.02}
    result = forward_head.classify(metrics)
    assert result.is_violation is False


def test_forward_head_violation():
    metrics = {"forward_head_amount": forward_head.THRESHOLD + 0.03}
    result = forward_head.classify(metrics)
    assert result.is_violation is True
    assert result.code == "FORWARD_HEAD"


def test_too_close_no_violation_when_delta_small():
    metrics = {"face_scale_delta": too_close.DELTA_THRESHOLD - 0.01}
    result = too_close.classify(metrics)
    assert result.is_violation is False


def test_too_close_violation_when_delta_large():
    metrics = {"face_scale_delta": too_close.DELTA_THRESHOLD + 0.03}
    result = too_close.classify(metrics)
    assert result.is_violation is True
    assert result.code == "TOO_CLOSE"


def test_leaning_on_arm_no_violation_when_far():
    metrics = {
        "hand_face_dist_left": leaning_on_arm.HAND_FACE_THRESHOLD + 0.1,
        "hand_face_dist_right": None,
    }
    result = leaning_on_arm.classify(metrics)
    assert result.is_violation is False


def test_leaning_on_arm_violation_when_close():
    metrics = {
        "hand_face_dist_left": leaning_on_arm.HAND_FACE_THRESHOLD - 0.05,
        "hand_face_dist_right": None,
    }
    result = leaning_on_arm.classify(metrics)
    assert result.is_violation is True
    assert result.code == "LEANING_ON_ARM"
