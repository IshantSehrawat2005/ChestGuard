"""
ChestGuard NeuralScan — X-Ray Analyzer
Core deep learning engine using DenseNet-121 from torchxrayvision.
"""
import torch
import torchxrayvision as xrv
import numpy as np
from PIL import Image
import io

# Singleton model instance
_model = None


def get_model():
    """Load the DenseNet-121 model (singleton pattern)."""
    global _model
    if _model is None:
        _model = xrv.models.DenseNet(weights="densenet121-res224-all")
        _model.eval()
    return _model


def preprocess_image(image_file):
    """
    Preprocess an uploaded image file for model inference.

    torchxrayvision expects:
    - Grayscale images
    - Pixel values in range [-1024, 1024]
    - Shape (1, 1, 224, 224)

    Returns: (preprocessed_tensor, original_normalized_array, img_resized_224)
    """
    img = Image.open(image_file).convert("L")
    img_array = np.array(img, dtype=np.float32)

    # Store original normalized to [0,1] for visualization only
    original_vis = img_array / 255.0

    # ── torchxrayvision preprocessing ──
    # Use xrv.datasets.normalize to map to [-1024, 1024]
    img_normalized = xrv.datasets.normalize(img_array, maxval=255, reshape=True)
    # img_normalized is now shape (1, H, W) in range [-1024, 1024]

    # Resize to 224x224
    from skimage.transform import resize as sk_resize
    img_224 = sk_resize(img_normalized[0], (224, 224), anti_aliasing=True, preserve_range=True)

    # Create tensor: (batch, channels, H, W)
    img_tensor = torch.from_numpy(img_224).float()
    img_tensor = img_tensor.unsqueeze(0).unsqueeze(0)  # (1, 1, 224, 224)

    # Also resize the visual image to 224x224 for overlay
    img_vis_224 = sk_resize(original_vis, (224, 224), anti_aliasing=True)

    return img_tensor, original_vis, img_vis_224


def analyze_xray(image_file):
    """
    Run the uploaded image through DenseNet-121.

    Returns:
        results: dict of {condition: probability%} sorted by probability
        img_tensor: preprocessed tensor for GradCAM
        img_resized: resized numpy array for visualization
    """
    img_tensor, original, img_resized = preprocess_image(image_file)
    model = get_model()

    with torch.no_grad():
        predictions = model(img_tensor)

    raw_probs = predictions[0].detach().numpy()
    disease_names = list(model.pathologies)

    # Get operating thresholds for clinical significance
    op_threshs = None
    if hasattr(model, 'op_threshs') and model.op_threshs is not None:
        op_threshs = model.op_threshs.numpy()

    results = {}

    # First pass: collect raw probs and determine which are above threshold
    findings = []
    for i, disease in enumerate(disease_names):
        raw_prob = float(raw_probs[i])  # Already in [0, 1] range
        thresh = float(op_threshs[i]) if op_threshs is not None else 0.05
        if thresh <= 0:
            thresh = 0.01
        is_positive = raw_prob >= thresh
        findings.append((disease, raw_prob, thresh, is_positive))

    # Sort by raw probability for ranking context
    findings_sorted = sorted(findings, key=lambda x: x[1], reverse=True)
    max_prob = max(f[1] for f in findings) if findings else 1.0
    max_prob = max(max_prob, 0.01)  # Avoid div by zero

    for disease, raw_prob, thresh, is_positive in findings:
        # Base score: normalize raw probability to a meaningful range
        # Use the max output as the reference point
        normalized = raw_prob / max_prob  # 0 to 1 relative to strongest finding

        if is_positive:
            # Above clinical threshold — this is a detected finding
            # Score range: 30% to 95% based on normalized strength
            calibrated = 30.0 + (normalized * 65.0)
        else:
            # Below threshold — not a significant finding
            # Score range: 1% to 25%
            ratio_to_thresh = raw_prob / thresh
            calibrated = min(ratio_to_thresh * 15.0, 25.0)

        results[disease] = round(max(calibrated, 0.5), 2)

    # Sort by probability (highest first)
    results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

    return results, img_tensor, img_resized


def get_pathology_index(condition_name):
    """Get the index of a pathology in the model's output."""
    model = get_model()
    pathologies = list(model.pathologies)
    try:
        return pathologies.index(condition_name)
    except ValueError:
        return None
