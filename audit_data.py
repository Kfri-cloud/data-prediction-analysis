"""Point-in-time metadata gate. Passing is necessary, not proof of no leakage."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def timestamp(value):
    value = str(value or "").strip()
    if not value:
        raise ValueError("missing timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed.astimezone(timezone.utc)


def check_point_in_time(row, cutoff, kind="news"):
    """Canonical format for later experiments; no guessed publication delays."""
    if kind not in ("news", "numeric"):
        raise ValueError("kind must be news or numeric")
    required = ["available_at", "source_url", "snapshot_sha256"]
    required += ["published_at"] if kind == "news" else ["released_at", "vintage_id"]
    missing = [key for key in required if not str(row.get(key, "") or "").strip()]
    if missing:
        return {"eligible": False, "reason": "missing:" + ",".join(missing)}
    try:
        origin = timestamp(cutoff)
        available = timestamp(row["available_at"])
        public = timestamp(row["published_at" if kind == "news" else "released_at"])
        if available < public:
            return {"eligible": False, "reason": "availability_before_publication"}
        if public > origin or available > origin:
            return {"eligible": False, "reason": "not_available_at_forecast_origin"}
    except (TypeError, ValueError):
        return {"eligible": False, "reason": "invalid_or_ambiguous_timestamp"}
    # A hash field does not prove a historical snapshot. Source verification is separate.
    return {"eligible": True, "reason": "metadata_gate_only_source_verification_still_required"}


def audit_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)
    kind = "numeric" if path.name == "Economy.csv" else "news"
    required = ["available_at", "source_url", "snapshot_sha256"]
    required += ["released_at", "vintage_id"] if kind == "numeric" else ["published_at"]
    missing = [field for field in required if field not in columns]
    starts = [row.get("start_date", "") for row in rows if row.get("start_date")]
    dates = [row.get("date", "") for row in rows if row.get("date")]
    return {
        "file": path.name, "rows": len(rows), "columns": columns,
        "reference_period_start_min": min(starts) if starts else None,
        "reference_period_start_max": max(starts) if starts else None,
        "canonical_missing_fields": missing,
        "canonical_complete_rows": sum(all(str(row.get(k, "") or "").strip() for k in required) for row in rows),
        "date_order_is_ascending": dates == sorted(dates) if dates else None,
        "duplicate_numeric_dates": len(dates) - len(set(dates)) if dates else None,
        "has_generated_predictions_column": "preds" in columns,
        "verdict": "NOT_READY_FOR_POINT_IN_TIME_CLAIM" if missing else "REQUIRES_SOURCE_VERIFICATION",
        "interpretation": "Missing fields in this export do not prove that the original study leaked information. They prevent this local audit from verifying historical availability from these files alone."
    }


def main():
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        payload = (ROOT / "data" / item["file"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError("Source hash mismatch: " + item["file"])
    audits = [audit_csv(ROOT / "data" / name) for name in
              ("Economy.csv", "Economy_report.csv", "Economy_search.csv")]
    result = {
        "repository_commit": manifest["repository_commit"],
        "input_hashes_verified": True,
        "files": audits,
        "forecast_models_trained": 0,
        "forecast_accuracy_measured": False,
        "global_verdict": "CURRENT_TARGET_VALIDITY_UNVERIFIED",
        "next_required_evidence": [
            "Verify news publication timestamps and original historical versions; reference periods are not availability timestamps.",
            "Obtain numeric release timestamps and as-of vintages, or explicitly limit the claim to a retrospective revised-data benchmark.",
            "Validate target-domain data and forecast origins before fixing time splits.",
            "Compare numeric-only versus numeric-plus-news using the frozen protocol; do not use preds as ground truth.",
            "Record live forecasts before outcomes are released to test present-day transfer."
        ]
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/data_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
