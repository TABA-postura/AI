from typing import Any, Dict

from app.services import pipeline


def _fake_detect(_image_bytes: bytes) -> Dict[str, Any]:
    # detector는 여기선 안 중요하니까, 최소 형태만
    return {"landmarks": {}}


def test_pipeline_good_posture(monkeypatch):
    # metrics: 아무 위반도 없는 상태
    def fake_compute(_posture_data: Dict[str, Any]) -> Dict[str, float]:
        return {"forward_head_amount": 0.01}

    def fake_update_baseline(_metrics: Dict[str, float]) -> None:
        return None

    def fake_apply_baseline(metrics: Dict[str, float]) -> Dict[str, float]:
        return metrics

    def fake_aggregate(_results):
        return {
            "state": "GOOD",
            "violations": [],
            "violation_details": [],
        }

    def fake_advise(_aggregate_result):
        return [{"code": "GOOD", "message": "ok", "content_id": None}]

    monkeypatch.setattr("app.services.detector.detect", _fake_detect)
    monkeypatch.setattr("app.services.metrics.compute", fake_compute)
    monkeypatch.setattr("app.services.calibration.update_baseline", fake_update_baseline)
    monkeypatch.setattr("app.services.calibration.apply_baseline", fake_apply_baseline)
    monkeypatch.setattr("app.services.aggregator.aggregate", fake_aggregate)
    monkeypatch.setattr("app.services.advisor.advise", fake_advise)

    result = pipeline.run(b"", user_id=1, session_id=1)

    assert result["state"] == "GOOD"
    assert result["violations"] == []
    assert result["advices"][0]["code"] == "GOOD"


def test_pipeline_unknown_state(monkeypatch):
    # 랜드마크가 부족한 경우 (신뢰할 수 없는 프레임)
    def fake_compute(_posture_data: Dict[str, Any]) -> Dict[str, float]:
        return {}

    def fake_aggregate(_results):
        return {
            "state": "UNKNOWN",
            "violations": [],
            "violation_details": [],
        }

    def fake_advise(_aggregate_result):
        return [{"code": "UNKNOWN", "message": "자세를 인식할 수 없습니다.", "content_id": None}]

    monkeypatch.setattr("app.services.detector.detect", _fake_detect)
    monkeypatch.setattr("app.services.metrics.compute", fake_compute)
    monkeypatch.setattr("app.services.aggregator.aggregate", fake_aggregate)
    monkeypatch.setattr("app.services.advisor.advise", fake_advise)

    result = pipeline.run(b"", user_id=1, session_id=1)

    assert result["state"] == "UNKNOWN"
    assert result["violations"] == []
    assert result["advices"][0]["code"] == "UNKNOWN"
    assert result["advices"][0]["message"] == "자세를 인식할 수 없습니다."

def test_pipeline_forward_head(monkeypatch):
    # metrics: 거북목 위반 상황
    def fake_compute(_posture_data: Dict[str, Any]) -> Dict[str, float]:
        return {"forward_head_amount": 0.2}

    def fake_update_baseline(_metrics: Dict[str, float]) -> None:
        return None

    def fake_apply_baseline(metrics: Dict[str, float]) -> Dict[str, float]:
        return metrics

    def fake_aggregate(_results):
        # 분류기 결과를 생략하고, 최종 상태만 고정해서 테스트
        return {
            "state": "WARN",
            "violations": ["FORWARD_HEAD"],
            "violation_details": [
                {"code": "FORWARD_HEAD", "confidence": 0.9, "severity": 3}
            ],
        }

    def fake_advise(_aggregate_result):
        return [
            {
                "code": "FORWARD_HEAD",
                "message": "거북목이 감지됐어요.",
                "content_id": "POSTURE_FORWARD_HEAD",
            }
        ]

    monkeypatch.setattr("app.services.detector.detect", _fake_detect)
    monkeypatch.setattr("app.services.metrics.compute", fake_compute)
    monkeypatch.setattr("app.services.calibration.update_baseline", fake_update_baseline)
    monkeypatch.setattr("app.services.calibration.apply_baseline", fake_apply_baseline)
    monkeypatch.setattr("app.services.aggregator.aggregate", fake_aggregate)
    monkeypatch.setattr("app.services.advisor.advise", fake_advise)

    result = pipeline.run(b"", user_id=1, session_id=1)

    assert result["state"] == "WARN"
    assert result["violations"] == ["FORWARD_HEAD"]
    assert result["advices"][0]["code"] == "FORWARD_HEAD"
