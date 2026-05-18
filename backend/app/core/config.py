from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./yunpu.db"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    refresh_token_expire_days: int = 7
    app_name: str = "云谱"
    app_version: str = "1.0.0"
    default_username: str = "admin"
    default_password: str = "admin123"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    upload_dir: str = "./uploads"
    max_upload_size: int = 5 * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()
