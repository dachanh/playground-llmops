from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProviderAnswer:
    provider: str
    model: str
    answer: str
    latency_ms: int
    fallback_reason: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        payload = {
            "provider": self.provider,
            "model": self.model,
            "answer": self.answer,
            "latency_ms": self.latency_ms,
        }
        if self.fallback_reason:
            payload["fallback_reason"] = self.fallback_reason
        return payload


@dataclass
class QueryResult:
    context: List[Dict[str, Any]]
    response: ProviderAnswer
    secondary: Optional[ProviderAnswer] = None

    def as_dict(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {"context": self.context, "response": self.response.as_dict()}
        if self.secondary:
            body["secondary"] = self.secondary.as_dict()
        return body
