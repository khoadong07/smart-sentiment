from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional  # ✅ Import thêm Optional

class Settings(BaseSettings):
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    MODEL: str = Field(..., env="MODEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
