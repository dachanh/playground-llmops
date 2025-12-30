from __future__ import annotations

from typing import Iterable

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import Settings


def build_embeddings(settings: Settings) -> OllamaEmbeddings:
    return OllamaEmbeddings(model=settings.ollama_model, base_url=settings.ollama_url)


def get_qdrant_client(settings: Settings) -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, prefer_grpc=False)


def ensure_collection(client: QdrantClient, collection_name: str, embeddings: OllamaEmbeddings) -> None:
    try:
        client.get_collection(collection_name)
        return
    except Exception:
        logger.info("Creating Qdrant collection {}", collection_name)
    dimension = len(embeddings.embed_query("dimension probe"))
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(size=dimension, distance=qmodels.Distance.COSINE),
    )


def upsert_documents(documents: Iterable[Document], settings: Settings) -> int:
    docs = list(documents)
    if not docs:
        return 0
    embeddings = build_embeddings(settings)
    client = get_qdrant_client(settings)
    ensure_collection(client, settings.rag_collection, embeddings)
    store = Qdrant(client=client, collection_name=settings.rag_collection, embeddings=embeddings)
    store.add_documents(docs)
    logger.info("Upserted {} documents into collection {}", len(docs), settings.rag_collection)
    return len(docs)


def get_vectorstore(settings: Settings) -> Qdrant:
    embeddings = build_embeddings(settings)
    client = get_qdrant_client(settings)
    return Qdrant(client=client, collection_name=settings.rag_collection, embeddings=embeddings)
