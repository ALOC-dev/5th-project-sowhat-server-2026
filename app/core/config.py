import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    GROQ_API_KEY = os.getenv(key="GROQ_API_KEY")
    GROQ_MODEL = os.getenv(key="GROQ_MODEL", default="llama-3.1-8b-instant")
    OPENAI_API_KEY = os.getenv(key="OPENAI_API_KEY")
    OPENAI_COMPLETION_MODEL = os.getenv(
        key="OPENAI_COMPLETION_MODEL", default="gpt-5.5"
    )
    OPENAI_EMBEDDING_MODEL = os.getenv(
        key="OPENAI_EMBEDDING_MODEL", default="text-embedding-3-small"
    )
    DATABASE_URL = os.getenv(key="DATABASE_URL")

    # 참고 링크 웹 검색용. 없으면 검색 없이 REFERENCE_LINKS 매핑만 사용한다.
    TAVILY_API_KEY = os.getenv(key="TAVILY_API_KEY")

    JWT_SECRET_KEY = os.getenv(key="JWT_SECRET_KEY", default="dev-secret-key")
    JWT_ALGORITHM = os.getenv(key="JWT_ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv(key="ACCESS_TOKEN_EXPIRE_MINUTES", default="30")
    )

    REFRESH_TOKEN_EXPIRE_DAYS = int(
        os.getenv(key="REFRESH_TOKEN_EXPIRE_DAYS", default="7")
    )

    COOKIE_SECURE = os.getenv(key="COOKIE_SECURE", default="False").lower() == "true"
    COOKIE_SAMESITE = os.getenv(key="COOKIE_SAMESITE", default="lax")

settings = Settings()