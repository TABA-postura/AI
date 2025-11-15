from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    AI 서버 헬스 체크용 엔드포인트.
    BE나 FE에서 'AI 서버 살아 있나?' 확인할 때 사용.
    """
    return {"status": "ok"}