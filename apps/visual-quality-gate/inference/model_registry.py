"""
Model Versioning and Dataset Provenance Registry for Product B.
Tracks ONNX model artifacts, SHA-256 hashes, dataset origins, and benchmark metrics.
"""

from typing import Any, Dict


class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {
            "yolov8n-defect-v1.2-quantized": {
                "model_id": "yolov8n-defect-v1.2-quantized",
                "format": "ONNX (Int8 Dynamic Quantized)",
                "sha256": "8f3d6b20a174c8901e4d36e2f1e29c67bc250917281f62b2e88a09b30c149d8a",
                "dataset_name": "industrial_surface_defects_v2",
                "dataset_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "num_classes": 4,
                "classes": ["surface_crack", "void_cavity", "dent_scratch", "color_defect"],
                "mAP_50": 0.879,
                "p50_latency_cpu_ms": 68.4,
                "active_production": True,
            }
        }

    def get_active_model(self) -> Dict[str, Any]:
        return self.models["yolov8n-defect-v1.2-quantized"]


model_registry = ModelRegistry()
