from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.core.config import Settings
from app.infrastructure import chunkers, db, vectorstore


def ingest_document(path: Path, settings: Settings, chunk_size: int | None = None, overlap: int | None = None) -> int:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    logger.info("Ingesting file {}", path)
    text = chunkers.load_text(path)
    docs = chunkers.chunk_text(
        text,
        source=path.name,
        chunk_size=chunk_size or settings.chunk_size,
        overlap=overlap or settings.chunk_overlap,
    )
    inserted = vectorstore.upsert_documents(docs, settings)
    for doc in docs:
        meta = doc.metadata or {}
        db.log_document_metadata(meta.get("source", path.name), meta.get("chunk_id", ""), meta.get("hash", ""))
    return inserted
