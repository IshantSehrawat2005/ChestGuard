"""
ChestGuard NeuralScan — Anatomical Region Analyzer
Segments X-ray into anatomical zones and provides per-region findings.
"""
import torch
import numpy as np
from core.xray_analyzer import get_model


# Anatomical region definitions (coordinates on 224x224 image)
# These approximate standard chest X-ray anatomy
ANATOMICAL_REGIONS = {
    "Right Upper Lung": {
        "coords": (0, 0, 112, 75),  # (x1, y1, x2, y2)
        "description": "Upper right lung field including apex",
        "color": "#4f46e5"
    },
    "Right Lower Lung": {
        "coords": (0, 75, 112, 180),
        "description": "Lower right lung field including base",
        "color": "#06b6d4"
    },
    "Left Upper Lung": {
        "coords": (112, 0, 224, 75),
        "description": "Upper left lung field including apex",
        "color": "#8b5cf6"
    },
    "Left Lower Lung": {
        "coords": (112, 75, 224, 180),
        "description": "Lower left lung field including base",
        "color": "#14b8a6"
    },
    "Cardiac Region": {
        "coords": (56, 60, 168, 170),
        "description": "Cardiac silhouette and mediastinum",
        "color": "#f43f5e"
    },
    "Costophrenic Angles": {
        "coords": (0, 170, 224, 224),
        "description": "Bilateral costophrenic angles and diaphragm",
        "color": "#f59e0b"
    }
}


def analyze_regions(img_tensor, img_resized):
    """
    Analyze each anatomical region independently.

    Args:
        img_tensor: preprocessed image tensor (1, 1, 224, 224)
        img_resized: resized numpy array (224, 224)

    Returns:
        dict of region analyses with top findings per region
    """
    model = get_model()
    disease_names = list(model.pathologies)
    region_results = {}

    for region_name, region_info in ANATOMICAL_REGIONS.items():
        x1, y1, x2, y2 = region_info["coords"]

        # Create masked image — zero out everything except the region
        masked_tensor = torch.zeros_like(img_tensor)
        masked_tensor[:, :, y1:y2, x1:x2] = img_tensor[:, :, y1:y2, x1:x2]

        # Run through model
        with torch.no_grad():
            predictions = model(masked_tensor)

        raw_probs = predictions[0].detach().numpy()

        # Get operating thresholds
        op_threshs = None
        if hasattr(model, 'op_threshs') and model.op_threshs is not None:
            op_threshs = model.op_threshs.numpy()

        # Get findings for this region
        region_findings = {}
        for i, disease in enumerate(disease_names):
            raw_prob = float(raw_probs[i])  # Already [0, 1]

            if op_threshs is not None:
                thresh = float(op_threshs[i])
                if thresh <= 0:
                    thresh = 0.01
                ratio = raw_prob / thresh
                if ratio < 0.5:
                    calibrated = ratio * 10.0
                elif ratio < 1.0:
                    calibrated = 5.0 + (ratio - 0.5) * 40.0
                elif ratio < 2.0:
                    calibrated = 25.0 + (ratio - 1.0) * 30.0
                elif ratio < 5.0:
                    calibrated = 55.0 + ((ratio - 2.0) / 3.0) * 30.0
                else:
                    calibrated = 85.0 + min((ratio - 5.0) / 10.0, 1.0) * 14.9
            else:
                calibrated = raw_prob * 100.0

            region_findings[disease] = round(min(calibrated, 99.9), 2)

        # Sort and take top findings
        region_findings = dict(
            sorted(region_findings.items(), key=lambda x: x[1], reverse=True)
        )

        # Calculate region health score (inverse of max abnormal finding)
        top_finding_prob = list(region_findings.values())[0]
        no_finding_prob = region_findings.get("No Finding", 0)

        if list(region_findings.keys())[0] == "No Finding":
            health_score = min(100, no_finding_prob + 20)
        else:
            health_score = max(0, 100 - top_finding_prob)

        region_results[region_name] = {
            "findings": dict(list(region_findings.items())[:3]),
            "health_score": round(health_score, 1),
            "description": region_info["description"],
            "color": region_info["color"],
            "coords": region_info["coords"],
            "status": _get_region_status(health_score)
        }

    return region_results


def _get_region_status(health_score):
    """Determine region status based on health score."""
    if health_score >= 80:
        return "normal"
    elif health_score >= 60:
        return "mild"
    elif health_score >= 40:
        return "moderate"
    else:
        return "concerning"


def get_region_overlay_data():
    """
    Get region coordinate data for frontend overlay rendering.
    Returns normalized coordinates (0-1 range) for responsive overlay.
    """
    overlay_data = {}
    for region_name, region_info in ANATOMICAL_REGIONS.items():
        x1, y1, x2, y2 = region_info["coords"]
        overlay_data[region_name] = {
            "x": x1 / 224,
            "y": y1 / 224,
            "width": (x2 - x1) / 224,
            "height": (y2 - y1) / 224,
            "color": region_info["color"]
        }
    return overlay_data
