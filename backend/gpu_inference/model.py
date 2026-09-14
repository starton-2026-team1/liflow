import asyncio
import logging
from threading import Lock

import torch
from peft import PeftModel
from transformers import AutoModelForMultimodalLM, AutoProcessor, BitsAndBytesConfig

from gpu_inference.config import settings

logger = logging.getLogger(__name__)

_model = None
_processor = None
_load_lock = Lock()
_inference_lock = asyncio.Lock()

SYSTEM_PROMPT = """당신은 독거인 생활 안전 모니터링 서비스의 보호자 지원 AI입니다.
제공된 센서 데이터에서 확인되는 사실과 추정을 구분하고 없는 사실은 만들지 마세요.
한국어로 간결하게 답하고 의료 진단이나 처방을 하지 마세요.
의식 저하, 호흡 곤란, 흉통, 마비, 심한 출혈 등 응급 징후가 의심되면
119 신고와 즉시 의료 도움을 안내하세요.
답변 마지막에는 반드시 '※ AI 답변은 의료 진단이나 처방을 대신하지 않습니다.'를 포함하세요."""


def cuda_available() -> bool:
    return torch.cuda.is_available()


def model_loaded() -> bool:
    return _model is not None


def _load_model():
    global _model, _processor
    if _model is not None:
        return _model, _processor
    if not cuda_available():
        raise RuntimeError("Gemma inference requires a CUDA GPU")

    with _load_lock:
        if _model is not None:
            return _model, _processor
        _processor = AutoProcessor.from_pretrained(
            settings.local_ai_base_model, trust_remote_code=True
        )
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        base_model = AutoModelForMultimodalLM.from_pretrained(
            settings.local_ai_base_model,
            quantization_config=quantization,
            device_map={"": 0},
            dtype=torch.float16,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        _model = PeftModel.from_pretrained(
            base_model, settings.local_ai_adapter_path
        )
        _model.eval()
        logger.info("Gemma adapter loaded from %s", settings.local_ai_adapter_path)
    return _model, _processor


def _generate(question: str, sensor_context: str) -> str:
    model, processor = _load_model()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{sensor_context}\n\n질문:\n{question}"},
    ]
    prompt = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = processor(text=prompt, return_tensors="pt")
    inputs = {key: value.to("cuda") for key, value in inputs.items()}
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=settings.local_ai_max_new_tokens,
            do_sample=False,
        )
    prompt_length = inputs["input_ids"].shape[1]
    return processor.tokenizer.decode(
        output[0][prompt_length:], skip_special_tokens=True
    ).strip()


async def generate(question: str, sensor_context: str) -> str:
    async with _inference_lock:
        answer = await asyncio.to_thread(_generate, question, sensor_context)
    if not answer:
        raise RuntimeError("Gemma returned an empty response")
    return answer
