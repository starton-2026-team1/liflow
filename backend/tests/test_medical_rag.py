import json
import os
import sys
from types import SimpleNamespace
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("GPU_AI_API_KEY", "x" * 32)
os.environ.setdefault("LOCAL_AI_ADAPTER_PATH", "/tmp/test-adapter")

from gpu_inference import medical_rag  # noqa: E402


class FakeEncoder:
    def encode(self, *_args: Any, **_kwargs: Any) -> np.ndarray:
        return np.array([[1.0, 0.0]], dtype=np.float32)


def test_medical_rag_returns_most_similar_document(
    tmp_path: Path, monkeypatch: Any
) -> None:
    np.save(
        tmp_path / "embeddings.npy",
        np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
    )
    documents = [
        {"question": "혈압 관리", "answer": "정기적으로 측정하세요.", "domain_name": "내과"},
        {"question": "시력 검사", "answer": "안과에서 검사하세요.", "domain_name": "안과"},
    ]
    (tmp_path / "documents.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in documents),
        encoding="utf-8",
    )
    monkeypatch.setattr(medical_rag.settings, "medical_rag_enabled", True)
    monkeypatch.setattr(medical_rag.settings, "medical_rag_index_path", str(tmp_path))
    monkeypatch.setattr(medical_rag.settings, "medical_rag_top_k", 1)
    monkeypatch.setattr(medical_rag.settings, "medical_rag_min_score", 0.42)
    monkeypatch.setattr(medical_rag, "_embeddings", None)
    monkeypatch.setattr(medical_rag, "_documents", None)
    monkeypatch.setattr(medical_rag, "_encoder", None)

    class FakeSentenceTransformer:
        def __new__(cls, *_args: Any, **_kwargs: Any) -> FakeEncoder:
            return FakeEncoder()

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )

    result = medical_rag.search_medical_knowledge("혈압은 어떻게 관리해?")

    assert "혈압 관리" in result
    assert "정기적으로 측정하세요." in result
    assert "시력 검사" not in result
