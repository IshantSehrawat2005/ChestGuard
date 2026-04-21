"""
ChestGuard NeuralScan — Temporal Progression Tracker
Tracks condition changes across multiple X-ray scans over time.
"""
from datetime import datetime
import numpy as np


# In-memory session storage for scan history
_scan_sessions = {}


def add_scan(session_id, results, neural_score, scan_label=None):
    """
    Add a new scan to the temporal tracking session.

    Args:
        session_id: unique session identifier
        results: dict of {condition: probability%}
        neural_score: NeuralScore result dict
        scan_label: optional label (e.g., "Pre-treatment")

    Returns:
        scan entry dict
    """
    if session_id not in _scan_sessions:
        _scan_sessions[session_id] = []

    scan_entry = {
        "id": len(_scan_sessions[session_id]) + 1,
        "timestamp": datetime.now().isoformat(),
        "label": scan_label or f"Scan #{len(_scan_sessions[session_id]) + 1}",
        "results": results,
        "neural_score": neural_score["score"],
        "risk_tier": neural_score["tier"]["level"],
        "top_findings": dict(list(results.items())[:5])
    }

    _scan_sessions[session_id].append(scan_entry)

    return scan_entry


def get_progression(session_id):
    """
    Get progression data for all scans in a session.

    Returns:
        dict with timeline data, deltas, and alerts
    """
    scans = _scan_sessions.get(session_id, [])

    if len(scans) < 1:
        return {"scans": [], "deltas": [], "alerts": [], "has_data": False}

    if len(scans) < 2:
        return {
            "scans": scans,
            "deltas": [],
            "alerts": [],
            "has_data": True,
            "scan_count": 1
        }

    # Calculate deltas between consecutive scans
    deltas = []
    alerts = []

    for i in range(1, len(scans)):
        prev = scans[i - 1]
        curr = scans[i]

        scan_delta = {
            "from_scan": prev["label"],
            "to_scan": curr["label"],
            "from_timestamp": prev["timestamp"],
            "to_timestamp": curr["timestamp"],
            "neural_score_change": round(
                curr["neural_score"] - prev["neural_score"], 1
            ),
            "condition_changes": {}
        }

        # Compare conditions
        all_conditions = set(
            list(prev["results"].keys()) + list(curr["results"].keys())
        )

        for condition in all_conditions:
            prev_prob = prev["results"].get(condition, 0)
            curr_prob = curr["results"].get(condition, 0)
            change = round(curr_prob - prev_prob, 2)

            if abs(change) > 2:  # Only report meaningful changes
                scan_delta["condition_changes"][condition] = {
                    "previous": prev_prob,
                    "current": curr_prob,
                    "change": change,
                    "direction": "increased" if change > 0 else "decreased",
                    "significant": abs(change) > 10
                }

                # Generate alerts for significant changes
                if abs(change) > 10 and condition != "No Finding":
                    alert_type = "warning" if change > 0 else "improvement"
                    alerts.append({
                        "type": alert_type,
                        "condition": condition,
                        "change": change,
                        "message": (
                            f"{condition} {'increased' if change > 0 else 'decreased'} "
                            f"by {abs(change)}% between {prev['label']} and {curr['label']}"
                        )
                    })

        deltas.append(scan_delta)

    # Build timeline data for chart
    timeline_data = _build_timeline_chart_data(scans)

    return {
        "scans": scans,
        "deltas": deltas,
        "alerts": alerts,
        "has_data": True,
        "scan_count": len(scans),
        "timeline_chart": timeline_data
    }


def _build_timeline_chart_data(scans):
    """Build chart-ready timeline data."""
    # Get all conditions that appear in top 5 of any scan
    all_top_conditions = set()
    for scan in scans:
        for condition in list(scan["top_findings"].keys())[:5]:
            all_top_conditions.add(condition)

    # Build datasets
    labels = [scan["label"] for scan in scans]
    datasets = {}

    for condition in all_top_conditions:
        datasets[condition] = []
        for scan in scans:
            datasets[condition].append(scan["results"].get(condition, 0))

    # NeuralScore timeline
    neural_scores = [scan["neural_score"] for scan in scans]

    return {
        "labels": labels,
        "condition_datasets": datasets,
        "neural_scores": neural_scores
    }


def get_scan_count(session_id):
    """Get the number of scans in a session."""
    return len(_scan_sessions.get(session_id, []))


def clear_session(session_id):
    """Clear all scan data for a session."""
    if session_id in _scan_sessions:
        del _scan_sessions[session_id]
