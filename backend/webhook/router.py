"""
Webhook Router
==============
Receives GitHub webhook events and orchestrates the full
analysis pipeline for pull_request events.
"""
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException
from backend.webhook.validator import verify_github_signature
from backend.services.dependency_extractor import extract_dependency_changes
from backend.services.feature_engineer import engineer_features, features_to_vector
from backend.ml.preprocessor import Preprocessor
from backend.ml.predictor import RiskPredictor
from backend.ml.explainer import RiskExplainer
from backend.graph.trust_scorer import compute_batch_trust_scores
from backend.services.report_generator import generate_pr_report
from backend.utils.github_client import post_pr_comment
from backend.db.mongo import get_db
from backend.db.models import PackageRisk, ScanResult
from backend.config import get_settings
from backend.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Lazy-loaded singletons
_preprocessor: Preprocessor | None = None
_predictor: RiskPredictor | None = None
_explainer: RiskExplainer | None = None


def _get_ml_components():
    global _preprocessor, _predictor, _explainer
    if _preprocessor is None:
        _preprocessor = Preprocessor(settings.preprocessor_path)
    if _predictor is None:
        _predictor = RiskPredictor(settings.model_path)
    if _explainer is None:
        _explainer = RiskExplainer(
            model=_predictor.model,
            preprocessor=_preprocessor.pipeline,
        )
    return _preprocessor, _predictor, _explainer


@router.post("/webhook")
async def github_webhook(request: Request):
    body_bytes = await verify_github_signature(request)
    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(body_bytes)

    if event != "pull_request":
        return {"status": "ignored", "event": event}

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "action": action}

    pr = payload["pull_request"]
    repo = payload["repository"]
    installation_id = payload.get("installation", {}).get("id", 0)

    repo_full_name = repo["full_name"]
    pr_number = pr["number"]
    base_sha = pr["base"]["sha"]
    head_sha = pr["head"]["sha"]

    logger.info(f"Processing PR #{pr_number} in {repo_full_name}")

    # Run the analysis pipeline in background so we return 200 immediately
    asyncio.create_task(
        _run_analysis(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            base_sha=base_sha,
            head_sha=head_sha,
            installation_id=installation_id,
        )
    )

    return {"status": "accepted", "pr": pr_number, "repo": repo_full_name}


async def _run_analysis(
    repo_full_name: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    installation_id: int,
):
    """Full async analysis pipeline."""
    try:
        preprocessor, predictor, explainer = _get_ml_components()

        # 1. Extract dependency changes
        added, removed, changed = await extract_dependency_changes(
            repo_full_name, base_sha, head_sha, installation_id
        )

        # Only analyse added + changed packages
        packages_to_scan: dict[str, str] = {}
        packages_to_scan.update(added)
        packages_to_scan.update({k: v[1] for k, v in changed.items()})

        if not packages_to_scan:
            logger.info(f"No new/changed dependencies in PR #{pr_number}")
            return

        # 2. Feature engineering for all packages (concurrent)
        tasks = [
            engineer_features(name, version, dependency_depth=0)
            for name, version in packages_to_scan.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. ML prediction + explanation
        package_risks: list[PackageRisk] = []
        graph_input: list[dict] = []

        for (name, version), result in zip(packages_to_scan.items(), results):
            if isinstance(result, Exception):
                logger.error(f"Feature extraction failed for {name}: {result}")
                continue

            features, raw_data = result
            fv = features_to_vector(features)
            x_scaled = preprocessor.transform(fv)
            risk_prob, risk_level = predictor.predict(x_scaled)
            top_factors, shap_pairs = explainer.explain(x_scaled)

            package_risks.append(PackageRisk(
                package_name=name,
                version=version,
                risk_probability=risk_prob,
                risk_level=risk_level,
                top_risk_factors=top_factors,
                trust_score=0.5,  # will be updated after graph scoring
                features=features.model_dump(),
            ))

            graph_input.append({
                "name": name,
                "risk_probability": risk_prob,
                "raw_data": raw_data,
                "dependencies": [],
            })

        # 4. Graph trust scoring
        trust_scores, cluster_risks, graph_data = compute_batch_trust_scores(graph_input)
        for pkg in package_risks:
            pkg.trust_score = trust_scores.get(pkg.package_name, 0.5)

        # 5. Generate report
        report_md = generate_pr_report(
            repo_full_name, pr_number, package_risks, cluster_risks
        )

        # 6. Post PR comment
        comment_url = ""
        try:
            comment_url = await post_pr_comment(
                repo_full_name, pr_number, report_md, installation_id
            )
        except Exception as e:
            logger.error(f"Failed to post PR comment: {e}")

        # 7. Store results in MongoDB
        high = sum(1 for p in package_risks if p.risk_level == "HIGH")
        medium = sum(1 for p in package_risks if p.risk_level == "MEDIUM")
        low = sum(1 for p in package_risks if p.risk_level == "LOW")

        scan = ScanResult(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            installation_id=installation_id,
            packages_scanned=len(package_risks),
            high_risk_count=high,
            medium_risk_count=medium,
            low_risk_count=low,
            package_risks=package_risks,
            comment_posted=bool(comment_url),
            comment_url=comment_url,
        )

        db = get_db()
        doc = scan.model_dump(by_alias=True)
        doc.pop("_id", None)
        await db["scans"].insert_one(doc)

        # Store per-package records for continuous learning
        for pkg in package_risks:
            await db["packages"].update_one(
                {"package_name": pkg.package_name},
                {
                    "$set": {
                        "last_scanned": scan.scanned_at,
                        "latest_risk_level": pkg.risk_level,
                    },
                    "$inc": {"scan_count": 1},
                    "$push": {
                        "features_history": {
                            "$each": [pkg.features],
                            "$slice": -50,  # Keep last 50 entries
                        }
                    },
                    "$max": {"avg_risk_score": pkg.risk_probability},
                },
                upsert=True,
            )

        logger.info(
            f"Analysis complete for {repo_full_name}#{pr_number}: "
            f"{len(package_risks)} packages, HIGH={high}, MEDIUM={medium}, LOW={low}"
        )

    except Exception as e:
        logger.error(f"Pipeline error for {repo_full_name}#{pr_number}: {e}", exc_info=True)
