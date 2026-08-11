"""
Dependency Trust Graph
======================
Builds a NetworkX directed graph of packages and maintainers,
then propagates trust scores using PageRank.
"""
import networkx as nx
from typing import Dict, List, Any
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TrustGraph:
    """
    Nodes:
      - "pkg:<name>"   — npm packages
      - "mnt:<name>"   — maintainers

    Edges:
      - pkg → pkg      — dependency relationship
      - mnt → pkg      — maintainer owns package
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_package(
        self,
        name: str,
        risk_probability: float,
        metadata: Dict[str, Any],
    ):
        node_id = f"pkg:{name}"
        self.graph.add_node(
            node_id,
            kind="package",
            name=name,
            risk_probability=risk_probability,
            stars=metadata.get("github", {}).get("stars", 0),
            maintainer_count=metadata.get("npm", {}).get("maintainer_count", 0),
            cve_count=metadata.get("cve", {}).get("cve_count", 0),
        )
        # Add maintainer nodes and ownership edges
        maintainers: List[str] = metadata.get("npm", {}).get("maintainers", [])
        for mnt in maintainers:
            mnt_id = f"mnt:{mnt}"
            if not self.graph.has_node(mnt_id):
                self.graph.add_node(mnt_id, kind="maintainer", name=mnt)
            self.graph.add_edge(mnt_id, node_id, relation="maintains")

    def add_dependency(self, from_pkg: str, to_pkg: str):
        """Record that from_pkg depends on to_pkg."""
        self.graph.add_edge(f"pkg:{from_pkg}", f"pkg:{to_pkg}", relation="depends_on")

    def compute_trust_scores(self) -> Dict[str, float]:
        """
        Run PageRank on the graph.
        High PageRank → widely depended-upon / trusted.
        We invert it: trust_score = PageRank (higher is better).
        """
        if self.graph.number_of_nodes() == 0:
            return {}
        try:
            pr = nx.pagerank(self.graph, alpha=0.85, max_iter=200)
            # Normalise to [0, 1]
            max_pr = max(pr.values()) or 1.0
            return {node: round(v / max_pr, 4) for node, v in pr.items()}
        except nx.PowerIterationFailedConvergence:
            logger.warning("PageRank did not converge; returning uniform scores.")
            n = self.graph.number_of_nodes()
            return {node: 1.0 / n for node in self.graph.nodes()}

    def get_cluster_risk(self) -> List[Dict[str, Any]]:
        """Identify connected components with elevated average risk."""
        undirected = self.graph.to_undirected()
        clusters = []
        for component in nx.connected_components(undirected):
            pkg_nodes = [n for n in component if n.startswith("pkg:")]
            if not pkg_nodes:
                continue
            risks = [
                self.graph.nodes[n].get("risk_probability", 0.0)
                for n in pkg_nodes
            ]
            avg_risk = sum(risks) / len(risks)
            clusters.append({
                "packages": [n.replace("pkg:", "") for n in pkg_nodes],
                "avg_risk": round(avg_risk, 4),
                "size": len(pkg_nodes),
            })
        return sorted(clusters, key=lambda c: c["avg_risk"], reverse=True)

    def to_serializable(self) -> Dict[str, Any]:
        """Export graph as JSON-serialisable dict for the frontend."""
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **attrs})
        edges = []
        for src, dst, attrs in self.graph.edges(data=True):
            edges.append({"source": src, "target": dst, **attrs})
        return {"nodes": nodes, "edges": edges}
