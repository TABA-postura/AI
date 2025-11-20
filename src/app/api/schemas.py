from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class Violation(BaseModel):
    code: str = Field(..., description="자세 코드 (예: FORWARD_HEAD)")
    severity: int = Field(
        ...,
        ge=1,
        le=3,
        description="심각도 (1=낮음, 3=높음)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="해당 자세가 맞다고 보는 확률/신뢰도",
    )


class AdviceItem(BaseModel):
    code: str = Field(..., description="자세 코드 또는 GENERIC")
    message: str = Field(..., description="사용자에게 보여줄 코칭 문구")
    content_id: Optional[str] = Field(
        None,
        description="정보 페이지/스트레칭 컨텐츠 ID (연결용)",
    )


class AnalyzeResponse(BaseModel):
    state: Literal["GOOD", "WARN", "ERROR"] = Field(
        ...,
        description="전체 상태",
    )
    violations: List[str] = Field(
        default_factory=list,
        description="감지된 자세 코드 리스트 (우선순위 순)",
    )
    violation_details: List[Violation] = Field(
        default_factory=list,
        description="각 자세별 상세 정보 (severity, confidence)",
    )
    advices: List[AdviceItem] = Field(
        default_factory=list,
        description="화면에 노출할 코칭 문구 리스트",
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="디버깅/통계용 숫자 메트릭",
    )
    timestamp_ms: int = Field(
        ...,
        description="서버 기준 UNIX ms 타임스탬프",
    )

    class Config:
        orm_mode = True


class AnalyzeRequestMeta(BaseModel):
    """
    실제로는 multipart(FormData)로 받지만,
    FE/BE가 맞춰야 하는 공통 필드를 문서화용으로 정의.
    """
    userId: int
    sessionId: int
    reset: bool = False
