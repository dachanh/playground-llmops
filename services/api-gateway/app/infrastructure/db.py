from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from loguru import logger
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from app.core.config import Settings

_pool: Optional[SimpleConnectionPool] = None


def init_db(settings: Settings) -> None:
    """Initialize connection pool and ensure schema exists."""
    global _pool
    if _pool:
        return
    try:
        _pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=settings.database_url)
        _bootstrap_tables(_pool)
        logger.info("Postgres pool created")
    except OperationalError as exc:
        logger.warning("Could not connect to Postgres at startup: {}", exc)
        _pool = None


def _bootstrap_tables(pool: SimpleConnectionPool) -> None:
    ddl_statements = [
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
        """
        CREATE TABLE IF NOT EXISTS prompt_version (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          name TEXT,
          template TEXT,
          version INT,
          created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS llm_request_log (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          prompt_id UUID,
          provider TEXT,
          model TEXT,
          latency_ms INT,
          input_tokens INT,
          output_tokens INT,
          created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS document_metadata (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          source TEXT,
          chunk_id TEXT,
          hash TEXT,
          created_at TIMESTAMP DEFAULT NOW()
        );
        """,
    ]
    with get_conn(pool) as conn:
        with conn.cursor() as cur:
            for ddl in ddl_statements:
                cur.execute(ddl)
        conn.commit()


@contextmanager
def get_conn(pool: Optional[SimpleConnectionPool] = None):
    global _pool
    active_pool = pool or _pool
    conn = None
    try:
        conn = active_pool.getconn() if active_pool else None
        yield conn
    finally:
        if active_pool and conn:
            active_pool.putconn(conn)


def log_llm_request(
    provider: str,
    model: str,
    latency_ms: int,
    input_tokens: Optional[int],
    output_tokens: Optional[int],
) -> None:
    global _pool
    if not _pool:
        logger.debug("Skipping log_llm_request: Postgres pool not available")
        return
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO llm_request_log (provider, model, latency_ms, input_tokens, output_tokens)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (provider, model, latency_ms, input_tokens, output_tokens),
            )
        conn.commit()


def log_document_metadata(source: str, chunk_id: str, hash_value: str) -> None:
    global _pool
    if not _pool:
        logger.debug("Skipping log_document_metadata: Postgres pool not available")
        return
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO document_metadata (source, chunk_id, hash)
                VALUES (%s, %s, %s);
                """,
                (source, chunk_id, hash_value),
            )
        conn.commit()
