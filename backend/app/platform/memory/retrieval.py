"""Hybrid semantic + BM25 retrieval from the memories table."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.memory.embeddings import embed_text

# RRF fusion constant (higher = less effect of rank differences)
RRF_K = 60


async def semantic_search(
    session: AsyncSession,
    user_id: str,
    query_embedding: list[float],
    top_k: int = 20,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Cosine similarity search against pgvector index."""
    where_clauses = ["user_id = :user_id", "deleted_at IS NULL"]
    params: dict[str, Any] = {"user_id": user_id, "limit": top_k}

    if filters:
        if ct := filters.get("content_type"):
            where_clauses.append("content_type = :content_type")
            params["content_type"] = ct
        if topic := filters.get("topic"):
            where_clauses.append("topic = :topic")
            params["topic"] = topic
        if start := filters.get("start_date"):
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start
        if end := filters.get("end_date"):
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end

    where = " AND ".join(where_clauses)
    vec_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = text(f"""
        SELECT id, user_id, content, content_type, topic, metadata, created_at,
               1 - (embedding <=> '{vec_literal}'::vector) AS score
        FROM memories
        WHERE {where}
        ORDER BY embedding <=> '{vec_literal}'::vector
        LIMIT :limit
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def bm25_search(
    session: AsyncSession,
    user_id: str,
    query: str,
    top_k: int = 20,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Full-text search using PostgreSQL ts_rank (BM25-like)."""
    where_clauses = ["user_id = :user_id", "deleted_at IS NULL",
                     "to_tsvector('simple', content) @@ plainto_tsquery('simple', :query)"]
    params: dict[str, Any] = {"user_id": user_id, "query": query, "limit": top_k}

    if filters:
        if ct := filters.get("content_type"):
            where_clauses.append("content_type = :content_type")
            params["content_type"] = ct
        if topic := filters.get("topic"):
            where_clauses.append("topic = :topic")
            params["topic"] = topic

    where = " AND ".join(where_clauses)
    sql = text(f"""
        SELECT id, user_id, content, content_type, topic, metadata, created_at,
               ts_rank(to_tsvector('simple', content),
                       plainto_tsquery('simple', :query)) AS score
        FROM memories
        WHERE {where}
        ORDER BY score DESC
        LIMIT :limit
    """)

    result = await session.execute(sql, params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


def reciprocal_rank_fusion(
    result_lists: list[list[dict[str, Any]]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Merge multiple ranked lists via Reciprocal Rank Fusion."""
    scores: dict[str, float] = defaultdict(float)
    docs: dict[str, dict[str, Any]] = {}

    for ranked in result_lists:
        for rank, doc in enumerate(ranked, start=1):
            doc_id = str(doc["id"])
            scores[doc_id] += 1.0 / (RRF_K + rank)
            docs[doc_id] = doc

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    fused = []
    for doc_id in sorted_ids[:top_k]:
        doc = docs[doc_id]
        doc["rrf_score"] = scores[doc_id]
        fused.append(doc)
    return fused


async def hybrid_search(
    session: AsyncSession,
    user_id: str,
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run semantic + BM25 search and fuse results with RRF."""
    query_embedding = await embed_text(query)

    semantic_results, bm25_results = await _gather_searches(
        session, user_id, query, query_embedding, top_k * 4, filters
    )

    return reciprocal_rank_fusion([semantic_results, bm25_results], top_k=top_k)


async def _gather_searches(
    session: AsyncSession,
    user_id: str,
    query: str,
    query_embedding: list[float],
    pool: int,
    filters: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run both searches; they're I/O bound but share the same session."""
    semantic = await semantic_search(session, user_id, query_embedding, pool, filters)
    bm25 = await bm25_search(session, user_id, query, pool, filters)
    return semantic, bm25
