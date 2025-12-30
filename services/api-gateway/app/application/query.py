from __future__ import annotations

from typing import Dict, List

from langchain_core.documents import Document
from loguru import logger

from app.core.config import Settings
from app.domain.models import ProviderAnswer, QueryResult
from app.domain.prompt import BASE_PROMPT
from app.infrastructure import llm_providers, vectorstore


def _format_context(docs: List[Document]) -> str:
    formatted = []
    for doc in docs:
        meta = doc.metadata or {}
        formatted.append(f"[{meta.get('source','unknown')}:{meta.get('chunk_id','')}]\n{doc.page_content}")
    return "\n\n".join(formatted)


def _answer_with_ollama(prompt: str, settings: Settings) -> ProviderAnswer:
    result: Dict = llm_providers.run_ollama(prompt, settings)
    return ProviderAnswer(**result)


def _answer_with_chatgpt(prompt: str, settings: Settings, reason: str | None = None) -> ProviderAnswer:
    result: Dict = llm_providers.run_chatgpt(prompt, settings)
    return ProviderAnswer(fallback_reason=reason, **result)


def run_query(question: str, settings: Settings, top_k: int, mode: str = "default") -> QueryResult:
    store = vectorstore.get_vectorstore(settings)
    docs = store.similarity_search(question, k=top_k)
    prompt = BASE_PROMPT.format(context=_format_context(docs), question=question)

    if mode == "evaluate":
        primary = _answer_with_ollama(prompt, settings)
        secondary = _answer_with_chatgpt(prompt, settings) if settings.openai_api_key else None
        return QueryResult(context=[d.metadata for d in docs], response=primary, secondary=secondary)

    try:
        primary = _answer_with_ollama(prompt, settings)
        return QueryResult(context=[d.metadata for d in docs], response=primary)
    except Exception as exc:
        logger.warning("Ollama failed, attempting ChatGPT fallback: {}", exc)
        if not settings.openai_api_key:
            raise
        fallback = _answer_with_chatgpt(prompt, settings, reason=str(exc))
        return QueryResult(context=[d.metadata for d in docs], response=fallback)
