from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import posture
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import init_exception_handlers

ALLOWED_ORIGINS = [
    "https://taba-postura.com",
    "https://www.taba-postura.com",
    "http://localhost:5173",
    "http://localhost:3000",
]

def create_app() -> FastAPI:
    # 로깅 설정
    setup_logging()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(posture.router)
    # 전역 예외 핸들러 등록
    init_exception_handlers(app)
    return app


app = create_app()
