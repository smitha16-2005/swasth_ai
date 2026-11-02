from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "SwasthAI"
    app_version: str = "0.4.0"
    database_url: str = "sqlite:///./swasthai.db"
    groq_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()