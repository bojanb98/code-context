import inspect
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from falkordb.asyncio import FalkorDB
from falkordb.asyncio.graph import AsyncGraph
from loguru import logger

from core.graph import GraphEdge, GraphEdgeType


@dataclass(frozen=True)
class GraphNode:
    id: str
    content: str | None = None
    relative_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    language: str | None = None
    doc: str | None = None


class GraphService:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._db = FalkorDB(
            host=host,
            port=port,
            username=username,
            password=password,
        )
        self._node_label = "CodeChunk"
        self._relationship_pattern = "|".join(
            edge_type.value for edge_type in GraphEdgeType
        )
        logger.debug(
            "Initialized GraphService for %s:%s targeting label %s",
            host,
            port,
            self._node_label,
        )

    async def delete_graph(self, collection_name: str) -> None:
        graph = await self._graph(collection_name)
        logger.debug("Deleting FalkorDB graph %s", collection_name)
        delete_result = graph.delete()
        if inspect.isawaitable(delete_result):
            await delete_result

    async def add_nodes(
        self,
        collection_name: str,
        nodes: Iterable[str | GraphNode | Mapping[str, Any]],
    ) -> None:
        records = self._normalize_node_records(nodes)
        if not records:
            return
        graph = await self._graph(collection_name)
        logger.debug("Upserting %d nodes into %s", len(records), collection_name)
        query = f"""
            UNWIND $nodes AS node
            MERGE (n:{self._node_label} {{id: node.id}})
            SET n += node
        """
        await graph.query(query, params={"nodes": records})

    async def remove_nodes(self, collection_name: str, node_ids: Iterable[str]) -> None:
        ids = self._normalize_ids(node_ids)
        if not ids:
            return
        graph = await self._graph(collection_name)
        logger.debug("Removing %d nodes (detach) from %s", len(ids), collection_name)
        query = f"""
            UNWIND $ids AS node_id
            MATCH (n:{self._node_label} {{id: node_id}})
            DETACH DELETE n
        """
        await graph.query(query, params={"ids": ids})

    async def add_edges(self, collection_name: str, edges: Iterable[GraphEdge]) -> None:
        typed_edges: dict[GraphEdgeType, list[dict[str, str]]] = {}
        for edge in edges:
            if not edge.source_id or not edge.target_id:
                continue
            typed_edges.setdefault(edge.edge_type, []).append(
                {"source_id": edge.source_id, "target_id": edge.target_id}
            )
        if not typed_edges:
            return
        graph = await self._graph(collection_name)
        for edge_type, payload in typed_edges.items():
            logger.debug(
                "Upserting %d %s edges into %s",
                len(payload),
                edge_type.value,
                collection_name,
            )
            query = f"""
                UNWIND $edges AS edge
                MATCH (source:{self._node_label} {{id: edge.source_id}})
                MATCH (target:{self._node_label} {{id: edge.target_id}})
                MERGE (source)-[:{edge_type.value}]->(target)
            """
            await graph.query(query, params={"edges": payload})

    async def neighbors(
        self,
        collection_name: str,
        node_ids: Iterable[str],
        max_hops: int,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        ids = self._normalize_ids(node_ids)
        if not ids:
            return [], []
        if max_hops < 1:
            raise ValueError("max_hops must be >= 1")
        graph = await self._graph(collection_name)
        nodes = await self._neighbor_nodes(graph, ids, max_hops)
        edges = await self._neighbor_edges(graph, ids, max_hops)
        return nodes, edges

    async def neighbor_nodes(
        self,
        collection_name: str,
        node_ids: Iterable[str],
        max_hops: int,
    ) -> list[GraphNode]:
        nodes, _ = await self.neighbors(collection_name, node_ids, max_hops)
        return nodes

    async def get_nodes(
        self, collection_name: str, node_ids: Iterable[str]
    ) -> list[GraphNode]:
        ids = self._normalize_ids(node_ids)
        if not ids:
            return []
        graph = await self._graph(collection_name)
        return await self._fetch_nodes(graph, ids)

    async def _graph(self, collection_name: str) -> AsyncGraph:
        return self._db.select_graph(collection_name)

    async def _neighbor_nodes(
        self, graph: AsyncGraph, node_ids: list[str], max_hops: int
    ) -> list[GraphNode]:
        seen: set[str] = set()
        collected: list[GraphNode] = []
        query = f"""
            MATCH (start:{self._node_label})
            WHERE start.id IN $ids
            MATCH path = (start)-[:{self._relationship_pattern}*1..{max_hops}]-(neighbor)
            UNWIND nodes(path) AS node
            RETURN DISTINCT node.id AS node_id,
                            node.content AS content,
                            node.relative_path AS relative_path,
                            node.start_line AS start_line,
                            node.end_line AS end_line,
                            node.language AS language,
                            node.doc AS doc
        """
        result = await graph.query(query, params={"ids": node_ids})
        for row in result.result_set:
            graph_node = self._row_to_node(row)
            if graph_node is None:
                continue
            if graph_node.id in seen:
                continue
            seen.add(graph_node.id)
            collected.append(graph_node)
        return collected

    async def _neighbor_edges(
        self, graph: AsyncGraph, node_ids: list[str], max_hops: int
    ) -> list[GraphEdge]:
        seen: set[tuple[str, str, GraphEdgeType]] = set()
        collected: list[GraphEdge] = []
        query = f"""
            MATCH (start:{self._node_label})
            WHERE start.id IN $ids
            MATCH path = (start)-[:{self._relationship_pattern}*1..{max_hops}]-(neighbor)
            UNWIND relationships(path) AS rel
            RETURN DISTINCT startNode(rel).id AS source_id,
                            endNode(rel).id AS target_id,
                            type(rel) AS edge_type
        """
        result = await graph.query(query, params={"ids": node_ids})
        for row in result.result_set:
            if len(row) < 3:
                continue
            source_id, target_id, type_name = row
            if not source_id or not target_id or not type_name:
                continue
            try:
                edge_type = GraphEdgeType(str(type_name))
            except ValueError:
                logger.debug("Skipping unknown edge type %s", type_name)
                continue
            key = (str(source_id), str(target_id), edge_type)
            if key in seen:
                continue
            seen.add(key)
            collected.append(
                GraphEdge(
                    source_id=str(source_id),
                    target_id=str(target_id),
                    edge_type=edge_type,
                )
            )
        return collected

    @staticmethod
    def _normalize_ids(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        for value in values:
            if not value:
                continue
            if value in seen:
                continue
            seen.add(value)
        return list(seen)

    @staticmethod
    def _normalize_node_records(
        nodes: Iterable[str | GraphNode | Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        for node in nodes:
            record: dict[str, Any]
            if isinstance(node, GraphNode):
                record = {
                    "id": node.id,
                    "content": node.content,
                    "relative_path": (
                        str(node.relative_path)
                        if node.relative_path is not None
                        else None
                    ),
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "language": node.language,
                    "doc": node.doc,
                }
            elif isinstance(node, str):
                record = {"id": node}
            elif isinstance(node, Mapping):
                raw_id = node.get("id")
                if not raw_id:
                    continue
                record = dict(node)
                record["id"] = str(raw_id)
                relative_path = record.get("relative_path")
                if relative_path is not None:
                    record["relative_path"] = str(relative_path)
            else:
                continue

            node_id = record.get("id")
            if not node_id:
                continue
            normalized[node_id] = record
        return list(normalized.values())

    @staticmethod
    def _row_to_node(row: list[Any] | tuple[Any, ...] | None) -> GraphNode | None:
        if not row:
            return None
        node_id = row[0]
        if not node_id:
            return None
        return GraphNode(
            id=str(node_id),
            content=str(row[1]) if len(row) > 1 and row[1] is not None else None,
            relative_path=str(row[2]) if len(row) > 2 and row[2] is not None else None,
            start_line=int(row[3]) if len(row) > 3 and row[3] is not None else None,
            end_line=int(row[4]) if len(row) > 4 and row[4] is not None else None,
            language=str(row[5]) if len(row) > 5 and row[5] is not None else None,
            doc=str(row[6]) if len(row) > 6 and row[6] is not None else None,
        )

    async def _fetch_nodes(self, graph, node_ids: list[str]) -> list[GraphNode]:
        query = f"""
            MATCH (n:{self._node_label})
            WHERE n.id IN $ids
            RETURN n.id AS node_id,
                   n.content AS content,
                   n.relative_path AS relative_path,
                   n.start_line AS start_line,
                   n.end_line AS end_line,
                   n.language AS language,
                   n.doc AS doc
        """
        result = await graph.query(query, params={"ids": node_ids})
        nodes: list[GraphNode] = []
        for row in result.result_set:
            graph_node = self._row_to_node(row)
            if graph_node is None:
                continue
            nodes.append(graph_node)
        return nodes
