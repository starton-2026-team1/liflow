import hmac
import logging

from fastapi import Depends, FastAPI, Header, HTTPException, status

from gpu_inference.config import settings
from gpu_inference.model import cuda_available, generate, model_loaded
from gpu_inference.schemas import GenerateRequest, GenerateResponse

logger = logging.getLogger(__name__)
app = FastAPI(title="Starton GPU Inference", docs_url=None, redoc_url=None)


def verify_api_key(x_api_key: str = Header(default="")) -> None:
    if not hmac.compare_digest(x_api_key, settings.gpu_ai_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@app.get("/health")
async def health() -> dict[str, bool | str]:
    return {
        "status": "ok" if cuda_available() else "degraded",
        "cuda_available": cuda_available(),
        "model_loaded": model_loaded(),
    }


@app.post("/generate", response_model=GenerateResponse)
async def create_answer(
    data: GenerateRequest, _: None = Depends(verify_api_key)
) -> GenerateResponse:
    try:
        answer = await generate(data.question, data.sensor_context)
    except Exception as exc:
        logger.exception("Gemma generation failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPU inference is unavailable",
        ) from exc
    return GenerateResponse(answer=answer, model=settings.local_ai_base_model)
