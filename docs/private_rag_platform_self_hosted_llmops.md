# Private RAG Platform (Self-hosted LLMOps – Hybrid with ChatGPT)

> **Goal**: Build a production-grade **Retrieval-Augmented Generation (RAG)** platform that is **fully self-hosted**, but can **optionally integrate ChatGPT** as a hybrid LLM provider for fallback, premium quality, or evaluation.
>
> This project is designed as a **real LLMOps system**, not a demo.

---

## 1. Problem Statement

Organizations want to:
- Use LLMs with **internal/private data** (PDFs, DOCX, logs, databases)
- Avoid sending sensitive data to external SaaS by default
- Still leverage **ChatGPT** when higher quality or reliability is needed
- Observe, evaluate, and control LLM behavior in production

---

## 2. Solution Overview

This platform provides:
- **Self-hosted RAG** using Ollama + LangChain
- **Hybrid LLM routing** (Ollama ↔ ChatGPT)
- **Vector-based retrieval** for grounded answers
- **PostgreSQL-backed LLMOps layer** (logs, prompts, metrics)
- **Kubernetes-native deployment** for scale and isolation

---

## 3. High-Level Architecture

```
┌──────────┐
│  Client  │ (Web / API)
└────┬─────┘
     │
┌────▼──────────┐
│ API Gateway   │ (FastAPI)
└────┬──────────┘
     │
┌────▼──────────────┐
│ LLM Router        │
│ - Policy Engine   │
│ - Provider Select │
└────┬──────────────┘
     │
┌────▼──────────┐
│ RAG Service   │ (LangChain)
│ - Retriever   │
│ - Prompt      │
│ - Chain       │
└────┬──────────┘
     │
 ┌───▼──────┐     ┌──────────────┐
 │ VectorDB │     │ LLM Provider │
 │          │     │ - Ollama     │
 │          │     │ - ChatGPT    │
 └───┬──────┘     └──────────────┘
     │
┌────▼──────────┐
│ PostgreSQL    │
│ - prompts     │
│ - logs        │
│ - metrics     │
└───────────────┘
```

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| LLM Runtime | Ollama (Llama3, Qwen, Mistral), ChatGPT (OpenAI API) |
| Orchestration | LangChain |
| API Layer | FastAPI (Python) |
| Vector Database | Qdrant or Chroma |
| Metadata & Logs | PostgreSQL |
| Infrastructure | Kubernetes |
| Observability | Prometheus, Grafana |
| Packaging | Docker, Helm |

---

## 5. Hybrid LLM Routing Strategy

### 5.1 Routing Policies

Each request is routed based on **policy rules**:

- **Default** → Ollama (local, low cost)
- **Fallback** → ChatGPT (timeout / error)
- **Premium Mode** → ChatGPT (high-quality answers)
- **Evaluation Mode** → Run both models and compare

```
Request
 → Router Policy
   ├─ Ollama
   └─ ChatGPT
```

---

## 6. RAG Data Flow

### 6.1 Document Ingestion (Offline / Batch)

1. Upload documents
2. Text extraction
3. Chunking (sliding window)
4. Embedding generation
5. Store vectors + metadata

```
Document → Chunk → Embed → Vector DB
```

### 6.2 Query Flow (Online)

1. User query
2. Query embedding
3. Retrieve top-K chunks
4. Prompt construction
5. LLM generation
6. Log request & response

```
Query → Retrieve → Prompt → LLM → Answer
```

---

## 7. Database Design (PostgreSQL)

### 7.1 Prompt Versioning
```sql
CREATE TABLE prompt_version (
  id UUID PRIMARY KEY,
  name TEXT,
  template TEXT,
  version INT,
  created_at TIMESTAMP
);
```

### 7.2 LLM Request Logs
```sql
CREATE TABLE llm_request_log (
  id UUID PRIMARY KEY,
  prompt_id UUID,
  provider TEXT,
  model TEXT,
  latency_ms INT,
  input_tokens INT,
  output_tokens INT,
  created_at TIMESTAMP
);
```

### 7.3 Document Metadata
```sql
CREATE TABLE document_metadata (
  id UUID PRIMARY KEY,
  source TEXT,
  chunk_id TEXT,
  hash TEXT,
  created_at TIMESTAMP
);
```

---

## 8. LangChain RAG Design

### 8.1 Core Components
- Retriever
- PromptTemplate
- LLM Provider Adapter
- Output Parser

### 8.2 Pseudocode
```python
retriever = vectorstore.as_retriever(k=5)

chain = (
    retriever
    | prompt_template
    | llm
    | output_parser
)
```

---

## 9. LLMOps Capabilities

### 9.1 Prompt Versioning
- Multiple versions per prompt
- Safe rollback

### 9.2 Observability
- Latency
- Token usage
- Error rate
- Provider comparison

### 9.3 Evaluation
- LLM-as-a-Judge
- Golden dataset replay
- Regression detection

### 9.4 Model Strategy
- Default (Ollama)
- Fallback (ChatGPT)
- Canary rollout

---

## 10. Kubernetes Deployment

### 10.1 Services
```
- api-gateway
- llm-router
- rag-service
- embedding-worker
- ollama
- vector-db
```

### 10.2 Scaling Strategy
- HPA by QPS / latency
- Dedicated node pool for LLM workloads

---

## 11. Security & Compliance

- No external calls by default
- Explicit opt-in for ChatGPT
- NetworkPolicy isolation
- Full audit logging

---

## 12. Repository Structure

```
private-rag-platform/
 ├─ services/
 │   ├─ api-gateway/
 │   ├─ llm-router/
 │   ├─ rag-service/
 │   └─ embedding-worker/
 ├─ providers/
 │   ├─ ollama_provider.py
 │   └─ chatgpt_provider.py
 ├─ helm/
 ├─ migrations/
 ├─ docs/
 └─ Makefile
```

---

## 13. Roadmap

### Phase 1
- Basic RAG with Ollama

### Phase 2
- ChatGPT integration
- Prompt versioning

### Phase 3
- Evaluation pipeline
- Auto rollback & cost-aware routing

---

## 14. Proof of Concept (PoC) Implementation Plan

### 14.1 Objectives & Success Criteria
- Answer user questions against 1–3 private PDFs/DOCX with grounded citations.
- Default to Ollama; fall back to ChatGPT on timeouts/errors; capture latency + token usage in Postgres.
- One-command local bring-up (Docker Compose) and a single ingestion script; <30 minutes to first answer.

### 14.2 Minimal Architecture (local-first)
- Compose stack: `fastapi` (API + router + rag), `qdrant`, `postgres`, `ollama` (Llama3), optional `chatgpt`.
- Single FastAPI service exposes `/ingest` (offline) and `/query` (online) endpoints; LangChain chain inside.
- Persistence: Qdrant for vectors; Postgres tables from section 7 for prompts/logs/metadata.
- Observability: log to Postgres + console; simple Prometheus counters optional.

### 14.3 Compose Baseline
Create `docker-compose.poc.yaml`:
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    volumes: [ "ollama:/root/.ollama" ]
    ports: [ "11434:11434" ]
  qdrant:
    image: qdrant/qdrant:latest
    ports: [ "6333:6333" ]
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: rag
      POSTGRES_PASSWORD: rag
      POSTGRES_DB: rag
    ports: [ "5432:5432" ]
  api:
    build: services/api-gateway  # single FastAPI app with router + rag chain
    environment:
      DATABASE_URL: postgres://rag:rag@postgres:5432/rag
      QDRANT_URL: http://qdrant:6333
      OLLAMA_URL: http://ollama:11434
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
    depends_on: [ollama, qdrant, postgres]
volumes: { ollama: {} }
```

### 14.4 Bring-up & Data Ingestion
1. Pull model: `docker compose -f docker-compose.poc.yaml up -d ollama && ollama pull llama3`.
2. Start stack: `docker compose -f docker-compose.poc.yaml up -d`.
3. Install app deps (inside repo): `python -m venv .venv && source .venv/bin/activate && pip install fastapi uvicorn langchain qdrant-client psycopg2-binary pydantic loguru openai`.
4. Run migrations for tables in section 7 (e.g., `alembic upgrade head` or simple `psql` script).
5. Ingest a document (script `scripts/ingest.py`):
```bash
python scripts/ingest.py --path data/sample.pdf --collection private_docs --chunk-size 500 --overlap 50
```
6. Test query:
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query":"What does the policy say about security?"}'
```

### 14.5 Routing & Evaluation (PoC)
- Policy: try Ollama; on timeout/error, call ChatGPT if `OPENAI_API_KEY` is set; log which provider served the response.
- Add `provider` + `latency_ms` + `input_tokens` + `output_tokens` to `llm_request_log`.
- Optional A/B: if `mode=evaluate`, call both providers and store comparison result in Postgres.

### 14.6 Demo Flow Checklist
- `docker compose -f docker-compose.poc.yaml up -d` brings up infra.
- `scripts/ingest.py` loads a PDF into Qdrant; rows appear in `document_metadata`.
- `POST /query` returns grounded answer with snippet citations and records a row in `llm_request_log`.
- Kill Ollama to show fallback to ChatGPT; logs reflect provider switch.
- Simple Grafana dashboard (latency, token count) optional if time permits.

### 14.7 Timeline & Deliverables
- Day 1: Compose file, Postgres schema, Ollama + Qdrant running, ingestion script working.
- Day 2: Query endpoint with routing + logging; basic notebooks/tests for ingestion/query.
- Day 3: Fallback path, evaluation toggle, short demo script + README updates.

---

## 15. Conclusion

This project represents a **production-grade Hybrid LLMOps RAG Platform**:
- Privacy-first by default
- Flexible multi-LLM strategy
- Observable, testable, and scalable

Ideal for:
- Internal AI platforms
- Compliance-sensitive environments
- Senior / Principal Engineer portfolios

---

*End of document*
