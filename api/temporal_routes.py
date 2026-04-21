"""
ChestGuard NeuralScan — Temporal Tracking Routes
"""
from flask import Blueprint, request, jsonify, session
from core.temporal_tracker import get_progression, get_scan_count, clear_session

temporal_bp = Blueprint("temporal", __name__)


@temporal_bp.route("/api/temporal/progression", methods=["GET"])
def get_temporal_progression():
    """Get temporal progression data for the current session."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"has_data": False, "scan_count": 0})

    progression = get_progression(session_id)
    return jsonify(progression)


@temporal_bp.route("/api/temporal/count", methods=["GET"])
def get_count():
    """Get the number of scans in current session."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"count": 0})
    return jsonify({"count": get_scan_count(session_id)})


@temporal_bp.route("/api/temporal/clear", methods=["POST"])
def clear_temporal():
    """Clear temporal data for the current session."""
    session_id = session.get("session_id")
    if session_id:
        clear_session(session_id)
    return jsonify({"status": "cleared"})
