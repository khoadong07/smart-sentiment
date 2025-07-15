from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional  # ✅ Import thêm Optional

class Settings(BaseSettings):
    FIREWORKS_API_KEY: Optional[str] = Field(default=None, env="FIREWORKS_API_KEY")
    FIREWORKS_API_URL: str = Field(default="https://api.fireworks.ai", env="FIREWORKS_API_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
