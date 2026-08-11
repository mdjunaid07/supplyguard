from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# ── Package Feature Vector ────────────────────────────────────────────────────

class PackageFeatures(BaseModel):
    package_name: str
    version: str
    package_age_days: float = 0.0
    maintainer_count: int = 0
    maintainer_account_age: float = 0.0
    commits_per_month: float = 0.0
    release_frequency: float = 0.0
    version_spike_ratio: float = 0.0
    contributor_growth_rate: float = 0.0
    repo_popularity_score: float = 0.0
    ownership_change_flag: int = 0
    download_trend_score: float = 0.0
    cve_count: int = 0
    cve_severity_score: float = 0.0
    dependency_depth: int = 0
    historical_risk_score: float = 0.0


# ── Scan / Prediction Result ──────────────────────────────────────────────────

class PackageRisk(BaseModel):
    package_name: str
    version: str
    risk_probability: float
    risk_level: str  # LOW | MEDIUM | HIGH
    top_risk_factors: List[str]
    trust_score: float
    features: Dict[str, Any]


class ScanResult(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    repo_full_name: str
    pr_number: int
    installation_id: int
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    packages_scanned: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    package_risks: List[PackageRisk]
    comment_posted: bool = False
    comment_url: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ── Package History (for continuous learning) ─────────────────────────────────

class PackageRecord(BaseModel):
    package_name: str
    last_scanned: datetime = Field(default_factory=datetime.utcnow)
    scan_count: int = 1
    avg_risk_score: float = 0.0
    latest_risk_level: str = "UNKNOWN"
    features_history: List[Dict[str, Any]] = []
    confirmed_malicious: Optional[bool] = None  # label for retraining
