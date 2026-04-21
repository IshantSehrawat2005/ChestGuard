"""
ChestGuard NeuralScan — Patient & History API Routes
Manages patient records, scan history, and database operations.
"""
import os
from flask import Blueprint, request, jsonify, send_file
from database import (
    get_all_patients, get_patient, delete_patient,
    get_patient_scans, get_scan, delete_scan,
    get_all_scans, get_dashboard_stats,
    get_chat_history, IMAGES_DIR
)

history_bp = Blueprint("history", __name__)


# ═════════════════════════════
# PATIENT ENDPOINTS
# ═════════════════════════════

@history_bp.route("/api/patients", methods=["GET"])
def list_patients():
    """List all patients with scan counts."""
    patients = get_all_patients()
    return jsonify({"patients": patients})


@history_bp.route("/api/patients/<int:patient_id>", methods=["GET"])
def get_patient_detail(patient_id):
    """Get a single patient with all their scans."""
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    scans = get_patient_scans(patient_id)
    return jsonify({"patient": patient, "scans": scans})


@history_bp.route("/api/patients/<int:patient_id>", methods=["DELETE"])
def remove_patient(patient_id):
    """Delete a patient and all associated data."""
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    delete_patient(patient_id)
    return jsonify({"status": "deleted", "patient_id": patient_id})


# ═════════════════════════════
# SCAN ENDPOINTS
# ═════════════════════════════

@history_bp.route("/api/scans", methods=["GET"])
def list_scans():
    """List all recent scans across all patients."""
    scans = get_all_scans()
    return jsonify({"scans": scans})


@history_bp.route("/api/scans/<int:scan_id>", methods=["GET"])
def get_scan_detail(scan_id):
    """Get full scan data including analysis results."""
    scan = get_scan(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({"scan": scan})


@history_bp.route("/api/scans/<int:scan_id>", methods=["DELETE"])
def remove_scan(scan_id):
    """Delete a single scan."""
    scan = get_scan(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404

    delete_scan(scan_id)
    return jsonify({"status": "deleted", "scan_id": scan_id})


@history_bp.route("/api/scans/<int:scan_id>/image", methods=["GET"])
def get_scan_image(scan_id):
    """Serve the saved X-ray image for a scan."""
    scan = get_scan(scan_id)
    if not scan or not scan.get("xray_filename"):
        return jsonify({"error": "Image not found"}), 404

    img_path = os.path.join(IMAGES_DIR, scan["xray_filename"])
    if not os.path.exists(img_path):
        return jsonify({"error": "Image file missing"}), 404

    return send_file(img_path)


@history_bp.route("/api/scans/<int:scan_id>/chat", methods=["GET"])
def get_scan_chat(scan_id):
    """Get chat history for a specific scan."""
    messages = get_chat_history(scan_id)
    return jsonify({"messages": messages})


# ═════════════════════════════
# DASHBOARD STATS
# ═════════════════════════════

@history_bp.route("/api/stats", methods=["GET"])
def dashboard_stats():
    """Get aggregate dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)
