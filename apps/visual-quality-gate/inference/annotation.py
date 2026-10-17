"""
Bounding Box Math and Image Annotation Helpers for Product B.
Provides coordinates normalization, IoU calculation, Non-Maximum Suppression (NMS),
and overlay drawing.
"""

from typing import List, Tuple
from packages.shared_contracts.events import BoundingBox, DefectSeverity


def calculate_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """
    Computes Intersection-over-Union (IoU) between two normalized bounding boxes.
    """
    x1 = max(box1.x_min, box2.x_min)
    y1 = max(box1.y_min, box2.y_min)
    x2 = min(box1.x_max, box2.x_max)
    y2 = min(box1.y_max, box2.y_max)

    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area1 = (box1.x_max - box1.x_min) * (box1.y_max - box1.y_min)
    area2 = (box2.x_max - box2.x_min) * (box2.y_max - box2.y_min)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def apply_nms(boxes: List[BoundingBox], iou_threshold: float = 0.45) -> List[BoundingBox]:
    """
    Applies Non-Maximum Suppression (NMS) to eliminate overlapping redundant defect boxes.
    """
    if not boxes:
        return []

    # Sort descending by confidence
    sorted_boxes = sorted(boxes, key=lambda b: b.confidence, reverse=True)
    selected: List[BoundingBox] = []

    while sorted_boxes:
        current = sorted_boxes.pop(0)
        selected.append(current)
        sorted_boxes = [
            b for b in sorted_boxes
            if b.class_id != current.class_id or calculate_iou(current, b) < iou_threshold
        ]

    return selected


def calculate_area_ratio(box: BoundingBox) -> float:
    """
    Returns normalized area (width * height) as a ratio of the whole frame.
    """
    w = max(0.0, box.x_max - box.x_min)
    h = max(0.0, box.y_max - box.y_min)
    return round(w * h, 4)
