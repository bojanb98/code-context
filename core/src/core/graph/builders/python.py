from tree_sitter import Node

from core.graph.builders.default import DefaultGraphBuilder


class PythonGraphBuilder(DefaultGraphBuilder):

    _ADDITIONAL_BINDING_FIELDS = {
        ("with_item", "alias"),
        ("except_clause", "name"),
        ("as_pattern", "alias"),
        ("capture_pattern", "name"),
    }

    def _is_binding_identifier(
        self, parent: Node | None, field_name: str | None
    ) -> bool:
        if parent is not None and field_name is not None:
            if (parent.type, field_name) in self._ADDITIONAL_BINDING_FIELDS:
                return True
            # Named expressions (walrus) introduce bindings in current scope.
            if parent.type == "named_expression" and field_name == "name":
                return True
        return super()._is_binding_identifier(parent, field_name)

    def _symbol_name_from_node(self, node: Node | None) -> str | None:
        if node is None:
            return None
        if node.type == "dotted_name":
            parts = [self._node_text(child) for child in node.named_children]
            dotted = ".".join(part for part in parts if part)
            return dotted or None
        return super()._symbol_name_from_node(node)

    def _owner_name(self, node: Node | None) -> str | None:
        names: list[str] = []
        current = node
        while current is not None:
            if current.type == "class_definition":
                name_node = current.child_by_field_name("name")
                name = self._node_text(name_node) if name_node is not None else ""
                if name:
                    names.append(name)
            current = current.parent
        if names:
            return ".".join(reversed(names))
        return super()._owner_name(node)
