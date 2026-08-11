"""
Trust Scorer
============
Orchestrates graph construction for a batch of scanned packages
and returns per-package trust scores.
"""
from typing import Dict, List, Any, Tuple
from backend.graph.trust_graph import TrustGraph
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def compute_batch_trust_scores(
    packages: List[Dict[str, Any]],
) -> Tuple[Dict[str, float], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Args:
        packages: list of dicts, each with keys:
            - name: str
            - risk_probability: float
            - raw_data: dict (npm/github/cve)
            - dependencies: list[str]   (direct deps of this package)

    Returns:
        trust_scores  — { package_name: score }
        cluster_risks — list of cluster dicts
        graph_data    — serialisable graph for frontend
    """
    graph = TrustGraph()

    for pkg in packages:
        graph.add_package(
            name=pkg["name"],
            risk_probability=pkg.get("risk_probability", 0.5),
            metadata=pkg.get("raw_data", {}),
        )
        for dep in pkg.get("dependencies", []):
            graph.add_dependency(pkg["name"], dep)

    all_scores = graph.compute_trust_scores()

    # Extract only package scores (not maintainer nodes)
    pkg_trust: Dict[str, float] = {}
    for key, score in all_scores.items():
        if key.startswith("pkg:"):
            pkg_trust[key.replace("pkg:", "")] = score

    # Fill missing packages with neutral score
    for pkg in packages:
        if pkg["name"] not in pkg_trust:
            pkg_trust[pkg["name"]] = 0.5

    cluster_risks = graph.get_cluster_risk()
    graph_data = graph.to_serializable()

    logger.info(
        f"Trust scores computed for {len(pkg_trust)} packages, "
        f"{len(cluster_risks)} clusters."
    )
    return pkg_trust, cluster_risks, graph_data
