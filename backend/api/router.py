"""
Frontend API Router
===================
REST endpoints consumed by the React dashboard.
"""
from fastapi import APIRouter, Query, HTTPException
from backend.db.mongo import get_db
from backend.utils.logger import get_logger
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/api")
logger = get_logger(__name__)


def _serialize(doc: dict) -> dict:
    """Convert MongoDB ObjectId to string for JSON serialization."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@router.get("/scans")
async def list_scans(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    risk_level: str | None = Query(None),
):
    """List recent scans with optional high/medium/low filter."""
    db = get_db()
    query = {}
    if risk_level:
        level = risk_level.upper()
        if level == "HIGH":
            query["high_risk_count"] = {"$gt": 0}
        elif level == "MEDIUM":
            query["medium_risk_count"] = {"$gt": 0}

    cursor = db["scans"].find(query).sort("scanned_at", -1).skip(skip).limit(limit)
    scans = []
    async for doc in cursor:
        scans.append(_serialize(doc))
    total = await db["scans"].count_documents(query)
    return {"scans": scans, "total": total, "skip": skip, "limit": limit}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str):
    """Get a specific scan by ID."""
    db = get_db()
    try:
        oid = ObjectId(scan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID")
    doc = await db["scans"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _serialize(doc)


@router.get("/packages")
async def list_packages(
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("avg_risk_score"),
):
    """List all tracked packages sorted by risk."""
    db = get_db()
    cursor = db["packages"].find({}).sort(sort_by, -1).limit(limit)
    packages = []
    async for doc in cursor:
        packages.append(_serialize(doc))
    return {"packages": packages}


@router.get("/packages/{name}")
async def get_package(name: str):
    """Get detailed data for a specific package."""
    db = get_db()
    doc = await db["packages"].find_one({"package_name": name})
    if not doc:
        raise HTTPException(status_code=404, detail="Package not found")
    return _serialize(doc)


@router.get("/stats/overview")
async def overview_stats():
    """Dashboard summary stats."""
    db = get_db()
    total_scans = await db["scans"].count_documents({})
    total_packages = await db["packages"].count_documents({})

    # High-risk packages
    high_risk = await db["packages"].count_documents({"latest_risk_level": "HIGH"})
    medium_risk = await db["packages"].count_documents({"latest_risk_level": "MEDIUM"})
    low_risk = await db["packages"].count_documents({"latest_risk_level": "LOW"})

    # Scans in last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_scans = await db["scans"].count_documents(
        {"scanned_at": {"$gte": seven_days_ago}}
    )

    return {
        "total_scans": total_scans,
        "total_packages": total_packages,
        "high_risk_packages": high_risk,
        "medium_risk_packages": medium_risk,
        "low_risk_packages": low_risk,
        "recent_scans_7d": recent_scans,
    }


@router.get("/stats/risk-trend")
async def risk_trend(days: int = Query(30, ge=7, le=90)):
    """Risk trend data for the last N days (for chart)."""
    db = get_db()
    since = datetime.utcnow() - timedelta(days=days)
    cursor = db["scans"].find(
        {"scanned_at": {"$gte": since}},
        {"scanned_at": 1, "high_risk_count": 1, "medium_risk_count": 1, "low_risk_count": 1},
    ).sort("scanned_at", 1)

    trend = []
    async for doc in cursor:
        trend.append({
            "date": doc["scanned_at"].isoformat(),
            "high": doc.get("high_risk_count", 0),
            "medium": doc.get("medium_risk_count", 0),
            "low": doc.get("low_risk_count", 0),
        })
    return {"trend": trend}


@router.get("/graph/data")
async def get_graph_data():
    """
    Return a simplified dependency graph for frontend visualization.
    Aggregated from recent scans.
    """
    db = get_db()
    # Get most recent 50 packages with their risk levels
    cursor = db["packages"].find({}).sort("last_scanned", -1).limit(50)
    nodes = []
    edges = []
    async for doc in cursor:
        nodes.append({
            "id": f"pkg:{doc['package_name']}",
            "name": doc["package_name"],
            "kind": "package",
            "risk_level": doc.get("latest_risk_level", "UNKNOWN"),
            "avg_risk_score": doc.get("avg_risk_score", 0),
            "scan_count": doc.get("scan_count", 0),
        })
    return {"nodes": nodes, "edges": edges}
