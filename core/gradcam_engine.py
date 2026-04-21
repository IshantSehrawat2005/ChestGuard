"""
ChestGuard NeuralScan — GradCAM Explainability Engine
Generates per-condition heatmaps showing where the AI focuses.
"""
import torch
import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image

from core.xray_analyzer import get_model


def _get_target_layer(model):
    """Get the last convolutional layer for GradCAM."""
    # For torchxrayvision DenseNet, the features module contains
    # DenseBlock + Transition layers. The last DenseBlock is best for GradCAM.
    try:
        # model.features is a Sequential of DenseBlock/Transition layers
        # Get the very last layer (usually a BatchNorm after the last DenseBlock)
        return model.features[-1]
    except Exception:
        last_conv = None
        for module in model.features.modules():
            if isinstance(module, torch.nn.Conv2d):
                last_conv = module
        return last_conv


class GradCAM:
    """
    GradCAM implementation for torchxrayvision DenseNet models.
    Properly manages hooks to avoid memory leaks and stacking.
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._hooks = []

    def _register_hooks(self):
        """Register forward and backward hooks (call before each use)."""
        self._remove_hooks()  # Clean up any existing hooks first

        def forward_hook(module, input, output):
            self.activations = output.detach().clone()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach().clone()

        self._hooks.append(
            self.target_layer.register_forward_hook(forward_hook)
        )
        self._hooks.append(
            self.target_layer.register_full_backward_hook(backward_hook)
        )

    def _remove_hooks(self):
        """Remove all registered hooks."""
        for hook in self._hooks:
            hook.remove()
        self._hooks = []

    def generate(self, input_tensor, target_index):
        """
        Generate GradCAM heatmap for a specific target class.

        Args:
            input_tensor: (1, 1, 224, 224) properly preprocessed tensor
            target_index: index of the target pathology

        Returns:
            numpy heatmap array or None
        """
        self._register_hooks()

        try:
            self.model.eval()

            # Clone tensor and enable gradients
            x = input_tensor.clone().detach().requires_grad_(True)

            # Forward pass
            output = self.model(x)

            # Zero all existing gradients
            self.model.zero_grad()
            if x.grad is not None:
                x.grad.zero_()

            # Backward pass for the target class
            target_score = output[0, target_index]
            target_score.backward(retain_graph=False)

            if self.gradients is None or self.activations is None:
                return None

            # Global average pooling of gradients
            weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)  # (1, C, 1, 1)

            # Weighted combination of activations
            cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # (1, 1, H, W)

            # ReLU — we only want positive influence
            cam = torch.relu(cam)

            # Convert to numpy
            cam = cam.squeeze().cpu().numpy()

            # Normalize to [0, 1]
            if cam.max() > 0:
                cam = cam / cam.max()

            return cam

        except Exception as e:
            print(f"  GradCAM generation error: {e}")
            return None

        finally:
            self._remove_hooks()
            self.gradients = None
            self.activations = None


def generate_heatmap(img_tensor, condition_name, condition_index, img_resized):
    """
    Generate a GradCAM heatmap for a specific condition.

    Args:
        img_tensor: preprocessed image tensor (1, 1, 224, 224)
        condition_name: name of the condition
        condition_index: index in model output
        img_resized: original resized image (224, 224) numpy array for overlay

    Returns:
        base64-encoded heatmap overlay image (PNG)
    """
    model = get_model()
    target_layer = _get_target_layer(model)

    if target_layer is None:
        print(f"  No target layer found, using fallback for {condition_name}")
        return _generate_fallback_heatmap(img_resized)

    try:
        cam = GradCAM(model, target_layer)
        heatmap = cam.generate(img_tensor, condition_index)

        if heatmap is None:
            print(f"  GradCAM returned None for {condition_name}, using fallback")
            return _generate_fallback_heatmap(img_resized)

        # Resize heatmap to match the visualization image (224x224)
        heatmap_resized = cv2.resize(heatmap, (224, 224), interpolation=cv2.INTER_LINEAR)

        # Apply a slight Gaussian blur for smoother visualization
        heatmap_resized = cv2.GaussianBlur(heatmap_resized, (11, 11), 0)

        # Re-normalize after blur
        if heatmap_resized.max() > 0:
            heatmap_resized = heatmap_resized / heatmap_resized.max()

        # Create overlay
        overlay = _create_overlay(img_resized, heatmap_resized)
        return overlay

    except Exception as e:
        print(f"  GradCAM error for {condition_name}: {e}")
        import traceback
        traceback.print_exc()
        return _generate_fallback_heatmap(img_resized)


def generate_all_heatmaps(img_tensor, results, img_resized, top_n=5):
    """
    Generate heatmaps for top N conditions.

    Returns:
        dict of {condition_name: base64_heatmap_image}
    """
    from core.xray_analyzer import get_pathology_index

    heatmaps = {}
    top_conditions = list(results.items())[:top_n]

    print(f"\n  Generating GradCAM heatmaps for {len(top_conditions)} conditions...")

    for condition_name, probability in top_conditions:
        idx = get_pathology_index(condition_name)
        if idx is not None:
            print(f"    → {condition_name} (prob={probability}%, idx={idx})")
            heatmap_b64 = generate_heatmap(
                img_tensor, condition_name, idx, img_resized
            )
            if heatmap_b64:
                heatmaps[condition_name] = heatmap_b64

    print(f"  GradCAM complete: {len(heatmaps)} heatmaps generated\n")
    return heatmaps


def _create_overlay(img_array, heatmap, colormap=cv2.COLORMAP_JET, alpha=0.45):
    """Create a colored heatmap overlay on the original image."""
    # Ensure image is in [0, 255] uint8 RGB
    if len(img_array.shape) == 2:
        img_rgb = np.stack([img_array] * 3, axis=-1)
    else:
        img_rgb = img_array.copy()

    # Scale to 0-255 if needed
    if img_rgb.max() <= 1.0:
        img_rgb = (img_rgb * 255).astype(np.uint8)
    else:
        img_rgb = img_rgb.astype(np.uint8)

    # Apply colormap to heatmap
    heatmap_uint8 = (heatmap * 255).astype(np.uint8)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, colormap)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

    # Only overlay where heatmap is significant (threshold low-activation pixels)
    mask = heatmap > 0.15
    mask_3ch = np.stack([mask] * 3, axis=-1)

    overlay = img_rgb.copy()
    blended = cv2.addWeighted(img_rgb, 1 - alpha, heatmap_colored, alpha, 0)
    overlay[mask_3ch] = blended[mask_3ch]

    # Encode to base64
    img_pil = Image.fromarray(overlay)
    buffer = BytesIO()
    img_pil.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return b64


def _generate_fallback_heatmap(img_resized):
    """Generate a simple intensity-based fallback heatmap when GradCAM fails."""
    heatmap = img_resized.copy()
    if heatmap.max() > 0:
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
    return _create_overlay(img_resized, heatmap, alpha=0.3)


def encode_image_to_base64(img_array):
    """Encode a numpy image array to base64 PNG string."""
    if img_array.max() <= 1.0:
        img_array = (img_array * 255).astype(np.uint8)

    if len(img_array.shape) == 2:
        img_pil = Image.fromarray(img_array, mode="L")
    else:
        img_pil = Image.fromarray(img_array)

    buffer = BytesIO()
    img_pil.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
