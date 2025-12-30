#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "services" / "api-gateway"))

from app.application.ingest import ingest_document
from app.core.config import get_settings
from app.infrastructure import db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest a document into Qdrant for the RAG PoC.")
    parser.add_argument("--path", required=True, help="Path to PDF/DOCX/TXT file.")
    parser.add_argument("--collection", default=None, help="Collection name (defaults to RAG_COLLECTION env).")
    parser.add_argument("--chunk-size", type=int, default=None, help="Chunk size override.")
    parser.add_argument("--overlap", type=int, default=None, help="Chunk overlap override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    if args.collection:
        settings.rag_collection = args.collection
    if args.chunk_size:
        settings.chunk_size = args.chunk_size
    if args.overlap:
        settings.chunk_overlap = args.overlap

    db.init_db(settings)
    inserted = ingest_document(Path(args.path), settings)
    print(f"Ingested {inserted} chunks into collection {settings.rag_collection}")


if __name__ == "__main__":
    main()
