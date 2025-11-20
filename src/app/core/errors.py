from typing import Any, Dict

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class BadInputError(Exception):
    def __init__(self, message: str = "잘못된 입력입니다.", detail: Any | None = None):
        self.message = message
        self.detail = detail


class ModelNotReadyError(Exception):
    def __init__(self, message: str = "모델이 아직 준비되지 않았습니다."):
        self.message = message


def init_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BadInputError)
    async def bad_input_handler(
        request: Request,
        exc: BadInputError,
    ) -> JSONResponse:
        logger.warning("BadInputError: %s", exc.message)
        return JSONResponse(
            status_code=400,
            content={
                "error": "bad_input",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(ModelNotReadyError)
    async def model_not_ready_handler(
        request: Request,
        exc: ModelNotReadyError,
    ) -> JSONResponse:
        logger.error("ModelNotReadyError: %s", exc.message)
        return JSONResponse(
            status_code=503,
            content={
                "error": "model_not_ready",
                "message": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        # 예상치 못한 에러는 stack trace까지 남김
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "서버 내부 오류가 발생했습니다.",
            },
        )
