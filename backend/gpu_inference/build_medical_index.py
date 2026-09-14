import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a KoMedQA semantic-search index")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()
    with args.source.open(encoding="utf-8") as source:
        documents = [json.loads(line) for line in source if line.strip()]
    model = SentenceTransformer(args.model, device=args.device)
    embeddings = model.encode(
        [document["question"] for document in documents],
        batch_size=args.batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    ).astype(np.float32)
    args.output.mkdir(parents=True, exist_ok=True)
    np.save(args.output / "embeddings.npy", embeddings)
    with (args.output / "documents.jsonl").open("w", encoding="utf-8") as target:
        for document in documents:
            target.write(json.dumps(document, ensure_ascii=False) + "\n")
    manifest = {
        "source": str(args.source),
        "model": args.model,
        "documents": len(documents),
        "dimensions": int(embeddings.shape[1]),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
