import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    GROQ_API_KEY = os.getenv(key="GROQ_API_KEY")
    GROQ_MODEL = os.getenv(key="GROQ_MODEL", default="llama-3.1-8b-instant")
    OPENAI_API_KEY = os.getenv(key="OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv(key="OPENAI_MODEL", default="gpt-5.5")


settings = Settings()
