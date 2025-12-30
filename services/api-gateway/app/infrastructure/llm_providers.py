from __future__ import annotations

import time
from typing import Dict, Optional

from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from loguru import logger

from app.core.config import Settings
from app.infrastructure.db import log_llm_request


def _extract_usage_tokens(response) -> (Optional[int], Optional[int]):
    meta = getattr(response, "response_metadata", {}) or {}
    usage = meta.get("token_usage") or meta.get("usage") or {}
    return usage.get("prompt_tokens"), usage.get("completion_tokens")


def run_ollama(prompt: str, settings: Settings) -> Dict:
    llm = Ollama(model=settings.ollama_model, base_url=settings.ollama_url, timeout=120)
    start = time.perf_counter()
    output = llm.invoke(prompt)
    latency_ms = int((time.perf_counter() - start) * 1000)
    in_tokens, out_tokens = _extract_usage_tokens(output)
    log_llm_request("ollama", settings.ollama_model, latency_ms, in_tokens, out_tokens)
    content = output if isinstance(output, str) else str(output)
    return {"provider": "ollama", "model": settings.ollama_model, "answer": content, "latency_ms": latency_ms}


def run_chatgpt(prompt: str, settings: Settings) -> Dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.chatgpt_model, temperature=0)
    start = time.perf_counter()
    response = llm.invoke(prompt)
    latency_ms = int((time.perf_counter() - start) * 1000)
    in_tokens, out_tokens = _extract_usage_tokens(response)
    log_llm_request("chatgpt", settings.chatgpt_model, latency_ms, in_tokens, out_tokens)
    content = response.content if hasattr(response, "content") else str(response)
    return {"provider": "chatgpt", "model": settings.chatgpt_model, "answer": content, "latency_ms": latency_ms}
