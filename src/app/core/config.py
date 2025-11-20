import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Postura AI Server"

    # AI 동작 관련
    target_fps: float = 3.0

    # 백엔드(Spring) 연동
    spring_base_url: str = "http://localhost:8080"
    spring_ai_log_path: str = "/ai/log"

    # 로깅
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    환경 변수에서 값을 읽어 Settings를 구성한다.
    .env를 쓰고 싶으면 uvicorn 실행 전에 환경변수만 잡아주면 됨.
    """
    return Settings(
        app_name=os.getenv("APP_NAME", "Postura AI Server"),
        target_fps=float(os.getenv("TARGET_FPS", "3.0")),
        spring_base_url=os.getenv("SPRING_BASE_URL", "http://localhost:8080"),
        spring_ai_log_path=os.getenv("SPRING_AI_LOG_PATH", "/ai/log"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


settings = get_settings()
