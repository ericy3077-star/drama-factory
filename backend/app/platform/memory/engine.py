"""MemoryOS — core memory engine with hybrid retrieval and knowledge graph."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.memory.embeddings import content_fingerprint, embed_text
from app.platform.memory.graph import create_edge, get_neighbours
from app.platform.memory.retrieval import hybrid_search


class Memory:
    """Lightweight DTO returned from MemoryEngine operations."""

    def __init__(self, row: dict[str, Any]) -> None:
        self.id: UUID = row["id"]
        self.user_id: str = row["user_id"]
        self.content: str = row["content"]
        self.content_type: str = row["content_type"]
        self.topic: str | None = row.get("topic")
        self.metadata: dict[str, Any] = row.get("metadata") or {}
        self.created_at: datetime = row["created_at"]
        self.rrf_score: float = row.get("rrf_score", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "content": self.content,
            "content_type": self.content_type,
            "topic": self.topic,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "rrf_score": self.rrf_score,
        }


class MemoryEngine:
    """
    Facade over pgvector + full-text + knowledge graph.

    All methods accept an async SQLAlchemy session injected by the caller
    so that transaction boundaries remain in application control.
    """

    async def store(
        self,
        session: AsyncSession,
        user_id: str,
        content: str,
        content_type: str,
        metadata: dict[str, Any] | None = None,
        topic: str | None = None,
    ) -> Memory:
        """
        Embed *content* and persist a new memory row.

        Deduplicates by SHA-256 fingerprint within the same user + content_type.
        Returns the existing row on duplicate instead of inserting twice.
        """
        fingerprint = content_fingerprint(content)

        # Dedup check
        dedup_sql = text("""
            SELECT id, user_id, content, content_type, topic, metadata, created_at
            FROM memories
            WHERE user_id = :uid AND fingerprint = :fp AND deleted_at IS NULL
            LIMIT 1
        """)
        existing = await session.execute(dedup_sql, {"uid": user_id, "fp": fingerprint})
        row = existing.mappings().first()
        if row:
            return Memory(dict(row))

        embedding = await embed_text(content)
        # Build vector literal from validated floats only — safe to interpolate
        vec_literal = "[" + ",".join(f"{float(x):.8g}" for x in embedding) + "]"
        memory_id = uuid4()

        import json as _json
        insert_sql = text(f"""
            INSERT INTO memories
                (id, user_id, content, content_type, topic, metadata, fingerprint, embedding)
            VALUES
                (:id, :uid, :content, :ctype, :topic, :meta::jsonb,
                 :fp, '{vec_literal}'::vector)
            RETURNING id, user_id, content, content_type, topic, metadata, created_at
        """)
        result = await session.execute(
            insert_sql,
            {
                "id": memory_id,
                "uid": user_id,
                "content": content,
                "ctype": content_type,
                "topic": topic,
                "meta": _json.dumps(metadata or {}),
                "fp": fingerprint,
            },
        )
        await session.commit()
        return Memory(dict(result.mappings().one()))

    async def recall(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[Memory]:
        """Hybrid semantic + BM25 retrieval, fused via RRF."""
        rows = await hybrid_search(session, user_id, query, top_k=top_k, filters=filters)
        return [Memory(r) for r in rows]

    async def connect(
        self,
        session: AsyncSession,
        node_a_id: UUID,
        node_b_id: UUID,
        relation_type: str,
        weight: float = 1.0,
    ) -> dict[str, Any]:
        """Create or update a directed edge in the knowledge graph."""
        return await create_edge(session, node_a_id, node_b_id, relation_type, weight)

    async def get_timeline(
        self,
        session: AsyncSession,
        user_id: str,
        topic: str,
        date_range: tuple[datetime, datetime] | None = None,
    ) -> list[Memory]:
        """Return memories for *topic* ordered by creation time."""
        where = ["user_id = :uid", "topic = :topic", "deleted_at IS NULL"]
        params: dict[str, Any] = {"uid": user_id, "topic": topic}

        if date_range:
            where.append("created_at BETWEEN :start AND :end")
            params["start"] = date_range[0]
            params["end"] = date_range[1]

        sql = text(f"""
            SELECT id, user_id, content, content_type, topic, metadata, created_at
            FROM memories
            WHERE {" AND ".join(where)}
            ORDER BY created_at ASC
        """)
        result = await session.execute(sql, params)
        return [Memory(dict(r)) for r in result.mappings().all()]

    async def get_related(
        self,
        session: AsyncSession,
        memory_id: UUID,
        depth: int = 2,
    ) -> list[Memory]:
        """Graph BFS from *memory_id* up to *depth* hops."""
        rows = await get_neighbours(session, memory_id, depth=depth)
        return [Memory(r) for r in rows]

    async def delete(
        self,
        session: AsyncSession,
        memory_id: UUID,
        user_id: str,
    ) -> bool:
        """Soft-delete a memory (set deleted_at timestamp)."""
        sql = text("""
            UPDATE memories
            SET deleted_at = now()
            WHERE id = :mid AND user_id = :uid AND deleted_at IS NULL
            RETURNING id
        """)
        result = await session.execute(sql, {"mid": memory_id, "uid": user_id})
        await session.commit()
        return result.rowcount > 0


# Module-level singleton
memory_engine = MemoryEngine()
