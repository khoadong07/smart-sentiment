from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError

load_dotenv()

class Settings(BaseSettings):
    GEMINI_API_KEY: str | None = Field(default=None, env="GEMINI_API_KEY")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    MODEL: str = Field(..., env="MODEL")  # Required field, raises error if None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def validate_model(cls, v):
        if not v:
            raise ValueError("MODEL environment variable must be set")
        return v