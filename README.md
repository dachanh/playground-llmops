# Private RAG Platform PoC

This repository contains a self-hosted RAG PoC described in `docs/private_rag_platform_self_hosted_llmops.md`. It runs a single FastAPI service backed by Ollama (default), Qdrant, and Postgres with an optional ChatGPT fallback.

## Quickstart (local)
1) Start infra:
```bash
docker compose -f docker-compose.poc.yaml up -d ollama
docker compose -f docker-compose.poc.yaml up -d qdrant postgres
docker exec -it $(docker ps --filter name=ollama --format '{{.ID}}') ollama pull llama3
docker compose -f docker-compose.poc.yaml up -d api
```
2) Install app deps locally (optional for scripts):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/api-gateway/requirements.txt
```
3) Ingest a document (mounted from `./data`):
```bash
python scripts/ingest.py --path data/sample.pdf --collection private_docs --chunk-size 500 --overlap 50
```
4) Query the API:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What does the policy say about security?"}'
```
5) Fallback to ChatGPT by setting `OPENAI_API_KEY` in your environment before starting the API container.

## Services
- `docker-compose.poc.yaml` – Ollama, Qdrant, Postgres, FastAPI (router + RAG).
- `services/api-gateway` – FastAPI app with `/ingest` and `/query`.
- `scripts/ingest.py` – CLI ingestion helper used for the PoC demo flow.

## Onion Architecture Layout
- `app/domain` – core contracts (prompt, response shapes).
- `app/application` – use cases (ingest, query orchestration).
- `app/infrastructure` – adapters (Qdrant, Ollama/ChatGPT, Postgres, chunkers).
- `app/api` – delivery layer (FastAPI HTTP surface).

## Kubernetes (Helm)
Package: `helm/private-rag-poc`
```bash
helm install rag-poc helm/private-rag-poc \
  --set image.repository=<your-api-image> \
  --set image.tag=<tag> \
  --set api.openai.apiKey=<optional-openai-key>  # or set api.openai.existingSecret
```
Services exposed: API (8000), Qdrant (6333), Postgres (5432), Ollama (11434). Ingress is optional via `values.yaml`.
