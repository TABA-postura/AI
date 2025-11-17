from typing import Any, Dict, List

# 코드별 코칭 문구 & 컨텐츠 ID 매핑
ADVICE_CATALOG: Dict[str, Dict[str, Any]] = {
    "GOOD": {
        "code": "GOOD",
        "message": "좋은 자세를 유지하고 있어요! 👏  잠깐씩 일어나서 스트레칭만 해 주면 완벽해요.",
        "content_id": None,
    },
    "UNEQUAL_SHOULDERS": {
        "code": "UNEQUAL_SHOULDERS",
        "message": "어깨 높이가 서로 달라요. 양쪽 어깨를 천천히 으쓱였다 내리면서 균형을 맞춰 볼까요?",
        "content_id": "POSTURE_UNEQUAL_SHOULDERS",
    },
    "UPPER_BODY_TILT": {
        "code": "UPPER_BODY_TILT",
        "message": "상체가 한쪽으로 기울어져 있어요. 엉덩이를 의자 가운데에 두고 양쪽 골반에 균등하게 힘을 실어 주세요.",
        "content_id": "POSTURE_UPPER_BODY_TILT",
    },
    "HEAD_TILT": {
        "code": "HEAD_TILT",
        "message": "머리가 한쪽으로 기울어져 있어요. 귀와 어깨 사이를 길게 늘리는 느낌으로 목을 세워 주세요.",
        "content_id": "POSTURE_HEAD_TILT",
    },
    "FORWARD_HEAD": {
        "code": "FORWARD_HEAD",
        "message": "거북목이 감지됐어요. 턱을 살짝 당기고, 머리가 어깨 위에 올라오도록 세워 주세요.",
        "content_id": "POSTURE_FORWARD_HEAD",
    },
    "TOO_CLOSE": {
        "code": "TOO_CLOSE",
        "message": "화면과 너무 가까워요. 눈과 모니터 사이를 한 뼘 정도로 유지해 주세요.",
        "content_id": "POSTURE_TOO_CLOSE",
    },
    "LEANING_ON_ARM": {
        "code": "LEANING_ON_ARM",
        "message": "한쪽 팔에 몸을 기대고 있어요. 팔로 턱을 괴는 습관은 목·어깨 비대칭을 만들 수 있어요.",
        "content_id": "POSTURE_LEANING_ON_ARM",
    },
    "ASYMMETRIC_POSTURE": {
        "code": "ASYMMETRIC_POSTURE",
        "message": "전체적으로 좌우 균형이 무너진 자세예요. 엉덩이, 어깨, 귀가 일직선이 되도록 한 번 다시 정렬해 보세요.",
        "content_id": "POSTURE_ASYMMETRIC",
    },
    "GENERIC_WARN": {
        "code": "GENERIC_WARN",
        "message": "자세 불균형이 감지됐어요. 상체를 세우고, 목과 어깨의 긴장을 한 번 풀어 주세요.",
        "content_id": None,
    },
}

def advise(aggregate_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    최종 상태 + 위반 코드 리스트를 기반으로 사용자에게 보여줄 코칭 메시지 리스트를 만든다.
    - state == GOOD이면 GOOD 메시지 한 개만 반환
    - 그렇지 않으면 가장 중요한 위반 1~2개에 대한 메시지를 반환
    """
    state = aggregate_result.get("state", "UNKNOWN")
    violations: List[str] = aggregate_result.get("violations", []) or []

    if state == "GOOD" or not violations:
        return [ADVICE_CATALOG["GOOD"]]

    advices: List[Dict[str, Any]] = []

    # 가장 중요한 위반 2개까지만 코칭 (UI 과부하 방지)
    for code in violations[:2]:
        advice = ADVICE_CATALOG.get(code)
        if advice is None:
            advice = ADVICE_CATALOG["GENERIC_WARN"]
        advices.append(advice)

    return advices