from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Starton API"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    device_api_key: str = "fridge-sensor-01"
    public_data_service_key: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    alert_check_interval_seconds: int = 60
    alert_check_start_hour: int = 0
    alert_check_end_hour: int = 24
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-6"

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
