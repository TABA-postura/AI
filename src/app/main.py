from fastapi import FastAPI

from app.api.routers import posture
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import init_exception_handlers


def create_app() -> FastAPI:
    # 로깅 설정
    setup_logging()

    app = FastAPI(title=settings.app_name)

    # 라우터 등록
    app.include_router(posture.router)

    # 전역 예외 핸들러 등록
    init_exception_handlers(app)

    return app


app = create_app()
