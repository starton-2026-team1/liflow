from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GpuSettings(BaseSettings):
    gpu_ai_api_key: str = Field(min_length=32)
    local_ai_base_model: str = "google/gemma-4-E2B-it"
    local_ai_adapter_path: str
    local_ai_max_new_tokens: int = 160

    model_config = SettingsConfigDict(env_file=".env.gpu", extra="ignore")


settings = GpuSettings()
