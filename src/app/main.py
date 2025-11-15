from fastapi import FastAPI
from app.api.routers import posture

app = FastAPI(
    title="Postura AI Server",
    description="웹캠 기반 자세 분석 AI 서버 (FastAPI)",
    version="0.1.0",
)

# 라우터 등록
app.include_router(posture.router, prefix="/posture", tags=["posture"])


@app.get("/")
async def root():
    return {"message": "Postura AI server is running"}