from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # GitHub App
    github_app_id: str = ""
    github_private_key_path: str = "./private-key.pem"
    github_webhook_secret: str = ""
    github_token: str = ""

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "supplyguard"

    # Server
    backend_port: int = 8000
    environment: str = "development"
    secret_key: str = "change-me"

    # ML — suppress pydantic "model_" namespace warning
    model_path: str = "./ml-model/models/model.pkl"
    preprocessor_path: str = "./ml-model/models/preprocessor.pkl"

    # External APIs
    nvd_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"               # silently skip unknown .env keys (VITE_*, GITHUB_CLIENT_*)
        protected_namespaces = ()      # allow model_path without warning


@lru_cache()
def get_settings() -> Settings:
    return Settings()
