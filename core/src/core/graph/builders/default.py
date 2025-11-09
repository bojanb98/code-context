from dataclasses import dataclass
from typing import Iterator, Literal, Sequence

from tree_sitter import Node

from core.splitters.types import CodeChunk

from .protocol import GraphBuilder
from .ref_constants import (
    ALIAS_PARENT_TYPES,
    ASSIGNMENT_PARENT_TYPES,
    CALL_NODE_TYPES,
    CATCH_PARENT_TYPES,
    IDENTIFIER_NODE_TYPES,
    IMPORT_ALIAS_PARENT_TYPES,
    LOOP_TARGET_PARENT_TYPES,
    MEMBER_ATTRIBUTE_FIELDS,
    MEMBER_NODE_TYPES,
    OWNER_NODE_TYPES,
    PARAMETER_PARENT_TYPES,
    PATTERN_PARENT_TYPES,
    SELF_RECEIVER_NAMES,
    TYPE_REFERENCE_NODE_TYPES,
)
from .types import GraphEdge, GraphEdgeType


@dataclass(frozen=True)
class _ReferenceCandidate:
    name: str
    kind: Literal["call", "identifier"]
    owner: str | None = None


@dataclass(frozen=True)
class _ChunkContext:
    definition_ids: set[int]
    bound_names: set[str]
    alias_map: dict[str, str]
    field_cache: dict[int, str | None]
    extra_candidates: list[_ReferenceCandidate]
    owner_name: str | None


class DefaultGraphBuilder(GraphBuilder):

    def build(
        self, chunks: Sequence[CodeChunk], include_intra_file_refs: bool = True
    ) -> list[GraphEdge]:
        if not chunks:
            return []
        symbol_index = self._build_symbol_index(chunks)
        return self._reference_edges(chunks, symbol_index, include_intra_file_refs)

    def _build_symbol_index(
        self, chunks: Sequence[CodeChunk]
    ) -> dict[tuple[str, str], list[tuple[CodeChunk, str | None]]]:
        index: dict[tuple[str, str], list[tuple[CodeChunk, str | None]]] = {}

        for ref in chunks:
            node = ref.node
            if node is None:
                continue
            for ident in self._definition_name_nodes(node):
                name = self._node_text(ident)
                if not name:
                    continue
                key = (str(ref.language), name)
                owner = self._owner_name(node)
                index.setdefault(key, []).append((ref, owner))

        return index

    def _reference_edges(
        self,
        chunks: Sequence[CodeChunk],
        symbol_index: dict[tuple[str, str], list[tuple[CodeChunk, str | None]]],
        include_intra_file_refs: bool,
    ) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        seen: set[tuple[GraphEdgeType, str, str]] = set()

        for ref in chunks:
            node = ref.node
            if node is None:
                continue
            context = self._chunk_context(node)

            for candidate in self._reference_candidates(node, context):
                if not candidate.name:
                    continue
                matches = symbol_index.get((str(ref.language), candidate.name))
                if not matches:
                    continue

                for target, owner in matches:
                    if candidate.owner and owner and owner != candidate.owner:
                        continue
                    if target.id == ref.id:
                        continue
                    same_file = target.file_path == ref.file_path
                    if same_file and not include_intra_file_refs:
                        continue

                    edge_type = (
                        GraphEdgeType.CALLS
                        if candidate.kind == "call"
                        else GraphEdgeType.USES
                    )
                    key = (edge_type, ref.id, target.id)
                    if key in seen:
                        continue
                    seen.add(key)
                    edges.append(
                        GraphEdge(
                            source_id=ref.id,
                            target_id=target.id,
                            edge_type=edge_type,
                        )
                    )

        return edges

    def _chunk_context(self, node: Node) -> _ChunkContext:
        definition_ids = {id(n) for n in self._definition_name_nodes(node)}
        field_cache = self._build_field_cache(node)
        bound_names: set[str] = set()
        alias_map: dict[str, str] = {}
        extra_candidates: list[_ReferenceCandidate] = []
        extra_seen: set[tuple[str, Literal["call", "identifier"]]] = set()

        for descendant in self._iter_named(node):
            if descendant.type not in IDENTIFIER_NODE_TYPES:
                continue
            name = self._node_text(descendant)
            if not name:
                continue
            parent = descendant.parent
            field_name = field_cache.get(id(descendant))
            if self._is_binding_identifier(parent, field_name):
                bound_names.add(name)
                alias_target = self._alias_target(parent, field_name)
                if alias_target and alias_target != name:
                    alias_map[name] = alias_target
                if self._is_import_binding(parent, field_name) and alias_target:
                    key = (alias_target, "identifier")
                    if key not in extra_seen:
                        extra_seen.add(key)
                        extra_candidates.append(
                            _ReferenceCandidate(name=alias_target, kind="identifier")
                        )
                continue

        owner_name = self._owner_name(node)
        return _ChunkContext(
            definition_ids=definition_ids,
            bound_names=bound_names,
            alias_map=alias_map,
            field_cache=field_cache,
            extra_candidates=extra_candidates,
            owner_name=owner_name,
        )

    def _reference_candidates(
        self, node: Node, context: _ChunkContext
    ) -> Iterator[_ReferenceCandidate]:
        for candidate in context.extra_candidates:
            yield candidate

        for descendant in self._iter_named(node):
            if id(descendant) in context.definition_ids:
                continue

            if descendant.type in CALL_NODE_TYPES:
                candidate = self._call_candidate(descendant, context)
                if candidate is not None:
                    yield candidate
                continue

            if descendant.type in MEMBER_NODE_TYPES:
                if self._is_call_function_node(descendant):
                    continue
                candidate = self._member_candidate(
                    descendant, context, kind="identifier"
                )
                if candidate is not None:
                    yield candidate
                continue

            if descendant.type in IDENTIFIER_NODE_TYPES:
                candidate = self._identifier_candidate(descendant, context)
                if candidate is not None:
                    yield candidate
                continue

            if descendant.type in TYPE_REFERENCE_NODE_TYPES:
                candidate = self._type_reference_candidate(descendant)
                if candidate is not None:
                    yield candidate

    def _call_candidate(
        self, node: Node, context: _ChunkContext
    ) -> _ReferenceCandidate | None:
        func = (
            node.child_by_field_name("function")
            or node.child_by_field_name("name")
            or self._find_first_identifier(node)
        )
        if func is None:
            return None
        if func.type in MEMBER_NODE_TYPES:
            return self._member_candidate(func, context, kind="call")
        name = self._node_text(func)
        if not name:
            return None
        target = context.alias_map.get(name, name)
        return _ReferenceCandidate(name=target, kind="call")

    def _member_candidate(
        self, node: Node, context: _ChunkContext, *, kind: Literal["call", "identifier"]
    ) -> _ReferenceCandidate | None:
        base = (
            node.child_by_field_name("object")
            or node.child_by_field_name("value")
            or node.child_by_field_name("operand")
            or node.child_by_field_name("receiver")
        )
        attr = (
            node.child_by_field_name("attribute")
            or node.child_by_field_name("property")
            or node.child_by_field_name("name")
            or self._find_first_identifier(node)
        )
        if attr is None:
            return None
        attr_name = self._node_text(attr)
        if not attr_name:
            return None
        base_name = self._base_identifier_name(base)
        if base_name is None:
            return None
        owner = self._resolve_owner_for_base(base_name, context)
        if owner is None:
            return None
        return _ReferenceCandidate(name=attr_name, kind=kind, owner=owner)

    def _identifier_candidate(
        self, node: Node, context: _ChunkContext
    ) -> _ReferenceCandidate | None:
        name = self._node_text(node)
        if not name:
            return None
        parent = node.parent
        field_name = context.field_cache.get(id(node))
        if self._is_binding_identifier(parent, field_name):
            return None
        if self._is_member_attribute_identifier(parent, field_name):
            return None
        alias_target = context.alias_map.get(name)
        if alias_target:
            return _ReferenceCandidate(name=alias_target, kind="identifier")
        if name in context.bound_names:
            return None
        return _ReferenceCandidate(name=name, kind="identifier")

    def _type_reference_candidate(self, node: Node) -> _ReferenceCandidate | None:
        name_node = (
            node.child_by_field_name("type")
            or node.child_by_field_name("name")
            or self._find_first_identifier(node)
        )
        if name_node is None:
            return None
        name = self._node_text(name_node)
        if not name:
            return None
        return _ReferenceCandidate(name=name, kind="identifier")

    def _is_member_attribute_identifier(
        self, parent: Node | None, field_name: str | None
    ) -> bool:
        if parent is None or field_name is None:
            return False
        return (
            parent.type in MEMBER_NODE_TYPES and field_name in MEMBER_ATTRIBUTE_FIELDS
        )

    def _is_call_function_node(self, node: Node) -> bool:
        parent = node.parent
        if parent is None or parent.type not in CALL_NODE_TYPES:
            return False
        func = parent.child_by_field_name("function") or parent.child_by_field_name(
            "name"
        )
        return func is node

    def _build_field_cache(self, root: Node) -> dict[int, str | None]:
        cache: dict[int, str | None] = {}
        stack = [root]
        while stack:
            current = stack.pop()
            for index, child in enumerate(current.children):
                cache[id(child)] = current.field_name_for_child(index)
                stack.append(child)
        return cache

    def _is_binding_identifier(
        self, parent: Node | None, field_name: str | None
    ) -> bool:
        if parent is None:
            return False
        if parent.type in PARAMETER_PARENT_TYPES:
            return True
        if parent.type in PATTERN_PARENT_TYPES:
            return True
        if parent.type in ASSIGNMENT_PARENT_TYPES and (
            field_name in {"left", "name", "pattern", "identifier"}
        ):
            return True
        if parent.type in LOOP_TARGET_PARENT_TYPES and field_name in {
            "left",
            "value",
            "index",
            "name",
        }:
            return True
        if parent.type in CATCH_PARENT_TYPES:
            return True
        if parent.type == "keyword_argument" and field_name == "name":
            return True
        if parent.type in {"pair", "property_assignment"} and field_name in {
            "key",
            "property",
        }:
            return True
        if self._is_import_binding(parent, field_name):
            return True
        return False

    def _is_import_binding(self, parent: Node | None, field_name: str | None) -> bool:
        if parent is None or field_name is None:
            return False
        if parent.type in IMPORT_ALIAS_PARENT_TYPES and field_name == "alias":
            return True
        return False

    def _alias_target(self, parent: Node | None, field_name: str | None) -> str | None:
        if parent is None:
            return None
        if parent.type in ALIAS_PARENT_TYPES:
            rhs = (
                parent.child_by_field_name("value")
                or parent.child_by_field_name("right")
                or parent.child_by_field_name("initializer")
                or parent.child_by_field_name("assignment")
                or parent.child_by_field_name("expression")
            )
            return self._symbol_name_from_node(rhs)
        if parent.type in IMPORT_ALIAS_PARENT_TYPES and field_name == "alias":
            source = (
                parent.child_by_field_name("name")
                or parent.child_by_field_name("module")
                or parent.child_by_field_name("source")
                or parent.child_by_field_name("value")
            )
            return self._symbol_name_from_node(source)
        return None

    def _symbol_name_from_node(self, node: Node | None) -> str | None:
        if node is None:
            return None
        if node.type in IDENTIFIER_NODE_TYPES:
            return self._node_text(node)
        if node.type in {"dotted_name", "qualified_identifier", "scoped_identifier"}:
            if node.named_children:
                return self._symbol_name_from_node(node.named_children[-1])
            return self._node_text(node)
        if node.type in TYPE_REFERENCE_NODE_TYPES:
            inner = (
                node.child_by_field_name("type")
                or node.child_by_field_name("name")
                or self._find_first_identifier(node)
            )
            return self._node_text(inner) if inner is not None else None
        if node.type in CALL_NODE_TYPES:
            func = (
                node.child_by_field_name("function")
                or node.child_by_field_name("name")
                or self._find_first_identifier(node)
            )
            return self._node_text(func) if func is not None else None
        if node.type in MEMBER_NODE_TYPES:
            prop = (
                node.child_by_field_name("attribute")
                or node.child_by_field_name("property")
                or node.child_by_field_name("name")
            )
            if prop is not None:
                text = self._node_text(prop)
                if text:
                    return text
        return None

    def _base_identifier_name(self, node: Node | None) -> str | None:
        if node is None:
            return None
        if node.type in IDENTIFIER_NODE_TYPES:
            return self._node_text(node)
        if node.type in MEMBER_NODE_TYPES:
            inner = (
                node.child_by_field_name("object")
                or node.child_by_field_name("value")
                or node.child_by_field_name("operand")
                or node.child_by_field_name("receiver")
            )
            return self._base_identifier_name(inner)
        if node.type in CALL_NODE_TYPES:
            func = (
                node.child_by_field_name("function")
                or node.child_by_field_name("name")
                or self._find_first_identifier(node)
            )
            return self._base_identifier_name(func)
        return None

    def _resolve_owner_for_base(
        self, base_name: str, context: _ChunkContext
    ) -> str | None:
        if base_name in SELF_RECEIVER_NAMES:
            return context.owner_name
        if base_name in context.alias_map:
            return context.alias_map[base_name]
        if base_name in context.bound_names:
            return None
        return base_name

    def _owner_name(self, node: Node | None) -> str | None:
        current = node
        while current is not None:
            if current.type in OWNER_NODE_TYPES:
                name_node = current.child_by_field_name("name")
                name = self._node_text(name_node) if name_node is not None else ""
                if name:
                    return name
            current = current.parent
        return None

    def _definition_name_nodes(self, node: Node) -> list[Node]:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            return [name_node]
        fallback = self._find_first_identifier(node)
        return [fallback] if fallback is not None else []

    def _iter_named(self, node: Node) -> Iterator[Node]:
        stack = [node]
        while stack:
            current = stack.pop()
            yield current
            for child in reversed(current.named_children):
                stack.append(child)

    def _find_first_identifier(self, node: Node) -> Node | None:
        for descendant in self._iter_named(node):
            if descendant.type in IDENTIFIER_NODE_TYPES:
                return descendant
        return None

    def _node_text(self, node: Node | None) -> str:
        if node is None or node.text is None:
            return ""
        text = node.text.decode("utf-8").strip()
        return text
