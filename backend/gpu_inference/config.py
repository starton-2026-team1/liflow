from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GpuSettings(BaseSettings):
    gpu_ai_api_key: str = Field(min_length=32)
    local_ai_base_model: str = "google/gemma-4-E2B-it"
    local_ai_adapter_path: str
    local_ai_max_new_tokens: int = 160
    medical_rag_enabled: bool = False
    medical_rag_index_path: str = "/opt/starton/rag/index"
    medical_rag_model_name: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    medical_rag_top_k: int = 3
    medical_rag_min_score: float = 0.42
    medical_rag_max_context_chars: int = 6000

    model_config = SettingsConfigDict(env_file=".env.gpu", extra="ignore")


settings = GpuSettings()
