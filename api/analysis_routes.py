"""
ChestGuard NeuralScan — Analysis API Routes
Handles X-ray upload, analysis, heatmap, and region endpoints.
"""
import os
import uuid
import io
from flask import Blueprint, request, jsonify, session
from PIL import Image

from core.xray_analyzer import analyze_xray
from core.gradcam_engine import generate_all_heatmaps, encode_image_to_base64
from core.region_analyzer import analyze_regions, get_region_overlay_data
from core.risk_engine import calculate_neural_score
from core.temporal_tracker import add_scan
from agents.pipeline import run_full_pipeline
from database import save_patient, save_scan

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Main analysis endpoint.
    Accepts: multipart form with 'xray' file and patient info fields.
    Returns: complete analysis JSON including predictions, heatmaps,
             regions, risk score, and multi-agent pipeline results.
    """
    # Validate file
    if "xray" not in request.files:
        return jsonify({"error": "No X-ray image uploaded"}), 400

    file = request.files["xray"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Get patient info
    patient_info = {
        "name": request.form.get("name", ""),
        "age": request.form.get("age", "30"),
        "gender": request.form.get("gender", "Not specified"),
        "symptoms": request.form.get("symptoms", "None reported"),
        "smoking": request.form.get("smoking", "Never"),
        "conditions": request.form.get("conditions", "None reported")
    }

    try:
        # Read file into memory
        file_bytes = file.read()
        file_io = io.BytesIO(file_bytes)

        # ── Step 1: DenseNet Prediction ──
        results, img_tensor, img_resized = analyze_xray(file_io)

        # ── Step 2: GradCAM Heatmaps ──
        top_5 = dict(list(results.items())[:5])
        try:
            heatmaps = generate_all_heatmaps(img_tensor, results, img_resized, top_n=5)
        except Exception as e:
            print(f"GradCAM error: {e}")
            heatmaps = {}

        # ── Step 3: Original image as base64 ──
        original_b64 = encode_image_to_base64(img_resized)

        # ── Step 4: Region Analysis ──
        try:
            regions = analyze_regions(img_tensor, img_resized)
        except Exception as e:
            print(f"Region analysis error: {e}")
            regions = {}

        region_overlay = get_region_overlay_data()

        # ── Step 5: NeuralScore ──
        neural_score = calculate_neural_score(results, patient_info)

        # ── Step 6: Multi-Agent Pipeline ──
        try:
            pipeline_results = run_full_pipeline(
                results=results,
                top_findings=top_5,
                heatmap_conditions=list(heatmaps.keys()),
                patient_info=patient_info,
                neural_score_data=neural_score,
                region_data=regions
            )
        except Exception as e:
            print(f"Pipeline error: {e}")
            pipeline_results = {
                "agents": [],
                "status": "error",
                "errors": [str(e)],
                "recommendation": "Analysis pipeline encountered an error. Please try again."
            }

        # ── Step 7: Add to temporal tracker ──
        session_id = session.get("session_id", str(uuid.uuid4()))
        session["session_id"] = session_id
        scan_entry = add_scan(session_id, results, neural_score)

        # ── Step 8: Save to local database ──
        try:
            patient_id = save_patient(patient_info)
            scan_data = {
                "predictions": results,
                "top_findings": top_5,
                "neural_score": neural_score,
                "regions": regions,
                "pipeline": pipeline_results,
                "heatmaps": bool(heatmaps),
                "scan_label": scan_entry.get("label", "")
            }
            db_scan_id = save_scan(
                patient_id, scan_data,
                xray_file_bytes=file_bytes,
                original_filename=file.filename
            )
            session["current_scan_id"] = db_scan_id
            session["current_patient_id"] = patient_id
        except Exception as e:
            print(f"Database save error: {e}")
            db_scan_id = None
            patient_id = None

        # ── Build Response ──
        response = {
            "success": True,
            "predictions": results,
            "top_findings": top_5,
            "heatmaps": heatmaps,
            "original_image": original_b64,
            "regions": regions,
            "region_overlay": region_overlay,
            "neural_score": neural_score,
            "pipeline": pipeline_results,
            "scan_entry": scan_entry,
            "patient_info": patient_info,
            "db_patient_id": patient_id,
            "db_scan_id": db_scan_id
        }

        # Store in session for chat context
        session["analysis_context"] = {
            "top_findings": top_5,
            "neural_score": neural_score,
            "regions": regions,
            "recommendation": pipeline_results.get("recommendation", "")
        }
        session["patient_info"] = patient_info

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "success": False
        }), 500
