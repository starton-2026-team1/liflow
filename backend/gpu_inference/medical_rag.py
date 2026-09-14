import json
import logging
from pathlib import Path
from threading import Lock

import numpy as np

from gpu_inference.config import settings

logger = logging.getLogger(__name__)
_embeddings: np.ndarray | None = None
_documents: list[dict[str, str]] | None = None
_encoder = None
_load_lock = Lock()


def _load_index():
    global _embeddings, _documents, _encoder
    if _embeddings is not None:
        return _embeddings, _documents, _encoder
    with _load_lock:
        if _embeddings is not None:
            return _embeddings, _documents, _encoder
        index_dir = Path(settings.medical_rag_index_path)
        embeddings_path = index_dir / "embeddings.npy"
        documents_path = index_dir / "documents.jsonl"
        if not embeddings_path.is_file() or not documents_path.is_file():
            raise RuntimeError(f"Medical RAG index is missing: {index_dir}")
        embeddings = np.load(embeddings_path, mmap_mode="r")
        with documents_path.open(encoding="utf-8") as source:
            documents = [json.loads(line) for line in source if line.strip()]
        if embeddings.ndim != 2 or len(embeddings) != len(documents):
            raise RuntimeError("Medical RAG index files do not match")
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(settings.medical_rag_model_name, device="cpu")
        _embeddings = embeddings
        _documents = documents
        _encoder = encoder
        logger.info("Loaded %d medical RAG documents", len(documents))
    return _embeddings, _documents, _encoder


def search_medical_knowledge(question: str) -> str:
    if not settings.medical_rag_enabled:
        return ""
    embeddings, documents, encoder = _load_index()
    query = encoder.encode(
        [question], normalize_embeddings=True, convert_to_numpy=True
    )[0].astype(np.float32)
    scores = np.asarray(embeddings @ query, dtype=np.float32)
    candidate_count = min(settings.medical_rag_top_k, len(scores))
    if candidate_count == 0:
        return ""
    indices = np.argpartition(scores, -candidate_count)[-candidate_count:]
    indices = indices[np.argsort(scores[indices])[::-1]]
    passages: list[str] = []
    used_chars = 0
    for index in indices:
        if float(scores[index]) < settings.medical_rag_min_score:
            continue
        document = documents[int(index)]
        passage = (
            f"질문: {document['question']}\n"
            f"답변: {document['answer']}\n"
            f"분야: {document.get('domain_name', '의료 일반')}"
        )
        if used_chars + len(passage) > settings.medical_rag_max_context_chars:
            break
        passages.append(passage)
        used_chars += len(passage)
    return "\n\n".join(passages)
