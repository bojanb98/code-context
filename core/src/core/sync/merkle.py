import hashlib
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class MerkleDAGNode:
    id: str
    hash: str
    data: str
    parents: list[str]
    children: list[str]


class MerkleDAG:

    def __init__(self) -> None:
        self.nodes: dict[str, MerkleDAGNode] = {}
        self.root_ids: list[str] = []

    def _hash(self, data: str) -> str:
        """Generate SHA-256 hash of data.

        Args:
            data: Data to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def add_node(self, data: str, parent_id: str | None = None) -> str:
        """Add a node to the DAG.

        Args:
            data: Node data
            parent_id: Optional parent node ID

        Returns:
            ID of the added node
        """
        node_id = self._hash(data)

        node = MerkleDAGNode(
            id=node_id,
            hash=node_id,
            data=data,
            parents=[parent_id] if parent_id else [],
            children=[],
        )

        # If there's a parent, create the relationship
        if parent_id and parent_id in self.nodes:
            parent_node = self.nodes[parent_id]
            node.parents.append(parent_id)
            parent_node.children.append(node_id)
            self.nodes[parent_id] = parent_node
        elif not parent_id:
            # If no parent, it's a root node
            self.root_ids.append(node_id)

        self.nodes[node_id] = node
        return node_id

    def get_node(self, node_id: str) -> MerkleDAGNode | None:
        """Get a node by ID.

        Args:
            node_id: Node ID

        Returns:
            Node instance or None if not found
        """
        return self.nodes.get(node_id)

    def get_all_nodes(self) -> list[MerkleDAGNode]:
        """Get all nodes in the DAG.

        Returns:
            List of all nodes
        """
        return list(self.nodes.values())

    def get_root_nodes(self) -> list[MerkleDAGNode]:
        """Get all root nodes.

        Returns:
            List of root nodes
        """
        return [
            self.nodes[root_id] for root_id in self.root_ids if root_id in self.nodes
        ]

    def serialize(self) -> dict[str, Any]:
        """Serialize the DAG to a dictionary.

        Returns:
            Serializable dictionary representation
        """
        return {
            "nodes": [[node_id, asdict(node)] for node_id, node in self.nodes.items()],
            "root_ids": self.root_ids,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "MerkleDAG":
        """Deserialize DAG from dictionary.

        Args:
            data: Serialized DAG data

        Returns:
            Deserialized MerkleDAG instance
        """
        dag = cls()

        # Convert list format back to dict
        nodes_data = data.get("nodes", [])
        dag.nodes = {
            node_id: MerkleDAGNode(**node_data) for node_id, node_data in nodes_data
        }
        dag.root_ids = data.get("root_ids", [])

        return dag

    @staticmethod
    def compare(dag1: "MerkleDAG", dag2: "MerkleDAG") -> dict[str, list[str]]:
        """Compare two Merkle DAGs and find differences.

        Args:
            dag1: First DAG
            dag2: Second DAG

        Returns:
            Dictionary with keys 'added', 'removed', 'modified' containing lists of node IDs
        """
        nodes1 = {node.id: node for node in dag1.get_all_nodes()}
        nodes2 = {node.id: node for node in dag2.get_all_nodes()}

        # Find added nodes (in dag2 but not in dag1)
        added = [node_id for node_id in nodes2.keys() if node_id not in nodes1]

        # Find removed nodes (in dag1 but not in dag2)
        removed = [node_id for node_id in nodes1.keys() if node_id not in nodes2]

        # Find modified nodes (in both but with different data)
        modified = []
        for node_id, node1 in nodes1.items():
            node2 = nodes2.get(node_id)
            if node2 and node1.data != node2.data:
                modified.append(node_id)

        return {"added": added, "removed": removed, "modified": modified}

