from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Starton API"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    device_api_key: str = ""
    public_data_service_key: str = ""
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,https://localhost,capacitor://localhost"
    )
    alert_check_interval_seconds: int = 60
    alert_check_start_hour: int = 0
    alert_check_end_hour: int = 24
    monitoring_timezone: str = "Asia/Seoul"
    anthropic_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    )
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_max_tokens: int = 400
    local_ai_enabled: bool = False
    local_ai_api_url: str = ""
    local_ai_api_key: str = ""
    local_ai_timeout_seconds: float = 120.0
    web_push_vapid_public_key: str = ""
    web_push_vapid_private_key: str = ""
    web_push_vapid_subject: str = "mailto:admin@example.com"
    firebase_credentials_path: str = ""
    public_frontend_url: str = "http://ec2-32-236-226-35.ap-southeast-2.compute.amazonaws.com"
    nfc_contact_reveal_delay_minutes: int = 5

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
