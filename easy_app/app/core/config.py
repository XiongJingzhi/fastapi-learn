from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用程序配置类"""

    # 应用基本配置
    app_name: str = "FastAPI Learning App"
    debug: bool = False
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"

    # 数据库配置
    database_url: str

    # JWT 认证配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS 配置
    backend_cors_origins: List[str] = []

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """处理 CORS 源"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError("CORS origins must be a list or comma-separated string")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )


# 创建全局设置实例
settings = Settings()