"""Test the fixed analyzer with proper calibration."""
import sys, io
sys.path.insert(0, '.')

with open('saved_scans/scan_1_20260418_121512.jpeg', 'rb') as f:
    img_bytes = f.read()

lines = []
def log(msg=""):
    lines.append(msg)

from core.xray_analyzer import analyze_xray

file_io = io.BytesIO(img_bytes)
results, img_tensor, img_resized = analyze_xray(file_io)

log("=" * 65)
log("  CALIBRATED PREDICTIONS (Pneumonia X-ray)")
log("=" * 65)
log(f"\n{'#':>3s}  {'Condition':<32s} {'Score':>7s}  {'Bar'}")
log("-" * 65)

for i, (condition, prob) in enumerate(results.items()):
    bar = '#' * int(prob / 2)
    marker = " <<<" if condition == "Pneumonia" else ""
    log(f" {i+1:2d}. {condition:<32s} {prob:6.2f}%  {bar}{marker}")

log(f"\n  Tensor range: [{img_tensor.min():.0f}, {img_tensor.max():.0f}]")

# Test GradCAM
from core.gradcam_engine import generate_all_heatmaps
heatmaps = generate_all_heatmaps(img_tensor, results, img_resized, top_n=3)
log(f"\n  GradCAM heatmaps: {len(heatmaps)} generated")
for name, data in heatmaps.items():
    log(f"    - {name}: {len(data)//1024} KB")

log(f"\n  STATUS: {'PASS' if heatmaps else 'FAIL'}")

with open('test_results.txt', 'w') as f:
    f.write('\n'.join(lines))
print("Done - see test_results.txt")
