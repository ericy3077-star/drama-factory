"""Knowledge graph operations on the memory_edges table."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_edge(
    session: AsyncSession,
    node_a_id: UUID,
    node_b_id: UUID,
    relation_type: str,
    weight: float = 1.0,
) -> dict[str, Any]:
    """Insert a directed edge between two memory nodes (upsert by unique pair+type)."""
    sql = text("""
        INSERT INTO memory_edges (node_a_id, node_b_id, relation_type, weight)
        VALUES (:a, :b, :rel, :w)
        ON CONFLICT (node_a_id, node_b_id, relation_type)
        DO UPDATE SET weight = EXCLUDED.weight, updated_at = now()
        RETURNING *
    """)
    result = await session.execute(sql, {"a": node_a_id, "b": node_b_id, "rel": relation_type, "w": weight})
    await session.commit()
    return dict(result.mappings().one())


async def get_neighbours(
    session: AsyncSession,
    memory_id: UUID,
    depth: int = 2,
) -> list[dict[str, Any]]:
    """
    BFS up to *depth* hops from *memory_id*.
    Uses a recursive CTE so it works in plain PostgreSQL.
    """
    sql = text("""
        WITH RECURSIVE neighbours AS (
            SELECT node_b_id AS id, 1 AS depth
            FROM memory_edges
            WHERE node_a_id = :root AND deleted_at IS NULL
            UNION
            SELECT node_b_id AS id, depth + 1
            FROM   node_b_id AS id, depth + 1
            FROM   memory_edges me
            JOIN   neighbours n ON me.node_a_id = n.id
            WHERE  depth < :max_depth AND me.deleted_at IS NULL
        )
        SELECT DISTINCT m.*
        FROM neighbours nb
        JOIN memories m ON m.id = nb.id
        WHERE m.deleted_at IS NULL
        ORDER BY m.created_at DESC
    """)
    # Fix the double-alias bug in the CTE above — rewrite cleanly:
    sql = text("""
        WITH RECURSIVE neighbours(id, depth) AS (
            SELECT node_b_id, 1
            FROM   memory_edges
            WHERE  node_a_id = :root AND deleted_at IS NULL

            UNION ALL

            SELECT me.node_b_id, n.depth + 1
            FROM   memory_edges me
            JOIN   neighbours n ON me.node_a_id = n.id
            WHERE  n.depth < :max_depth AND me.deleted_at IS NULL
        )
        SELECT DISTINCT m.*
        FROM neighbours nb
        JOIN memories m ON m.id = nb.id
        WHERE m.deleted_at IS NULL
        ORDER BY m.created_at DESC
    """)
    result = await session.execute(sql, {"root": memory_id, "max_depth": depth})
    return [dict(row) for row in result.mappings().all()]


async def delete_edge(
    session: AsyncSession,
    node_a_id: UUID,
    node_b_id: UUID,
    relation_type: str,
) -> None:
    sql = text("""
        UPDATE memory_edges
        SET deleted_at = now()
        WHERE node_a_id = :a AND node_b_id = :b AND relation_type = :rel
    """)
    await session.execute(sql, {"a": node_a_id, "b": node_b_id, "rel": relation_type})
    await session.commit()
