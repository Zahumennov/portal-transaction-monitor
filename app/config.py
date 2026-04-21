from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str

    # Redis
    redis_url: str

    # Portal
    portal_base_url: str = "http://mock_portal:8001"

    # OpenCorporates
    opencorporates_api_url: str = "https://api.opencorporates.com/v0.4"

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()