from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./evolution.db"
    # For PostgreSQL: "postgresql+psycopg2://user:pass@localhost/evolution"


settings = Settings()
