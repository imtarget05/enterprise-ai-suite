"""
Safety Isolation Gate for Product B.
Guarantees that the LLM is restricted solely to advisory SOP explanations,
while deterministic mathematical and rule-based logic retains sole authority
over part release, quarantine, or rejection.
"""

from typing import Any, Dict, List
from packages.shared_contracts.events import BoundingBox, QualityVerdict
from apps.visual_quality_gate.backend.rules_engine import rules_engine


class QCSafetyGate:
    def decide_quality(self, defects: List[BoundingBox]) -> Dict[str, Any]:
        """
        Deterministic safety execution. Never calls LLM.
        """
        verdict, reasons, rule_evals = rules_engine.evaluate(defects)
        return {
            "verdict": verdict.value,
            "reasons": reasons,
            "rule_evaluations": rule_evals,
            "engine": "deterministic_safety_gate",
            "llm_involved": False,
        }

    def explain_defect_sop(self, defect_name: str, verdict: str) -> str:
        """
        Advisory-only SOP lookup. Does not modify verdict or release products.
        """
        sop_catalog = {
            "surface_crack": "SOP-QC-CRACK-01: Vết nứt bề mặt có thể gây nứt gãy chịu lực. Cách ly chi tiết vào khu vực Red Bin, chụp ảnh góc nghiêng 45 độ và chuyển cho Kỹ sư Luyện kim thẩm định.",
            "structural_porosity": "SOP-QC-POROSITY-02: Độ xốp / rỗ khí kết cấu (structural porosity) làm giảm độ bền mỏi. Cách ly chi tiết vào khu vực Red Bin và kiểm tra chụp X-quang công nghiệp (CT scan).",
            "void_cavity": "SOP-QC-VOID-02: Rỗ khí đúc vượt tiêu chuẩn yêu cầu kiểm tra siêu âm NDT (Non-Destructive Testing) để xác định độ sâu khuyết tật.",
            "dent_scratch": "SOP-QC-SCRATCH-03: Vết trầy xước nhẹ có thể xử lý đánh bóng lại (Rework) nếu chiều sâu < 0.2mm.",
            "color_defect": "SOP-QC-COLOR-04: Sai lệch màu sắc lớp mạ Anodized, cho phép xuất xưởng nếu nằm trong bảng màu Delta E < 2.0.",
        }
        return sop_catalog.get(defect_name, "SOP-QC-GENERIC: Kiểm tra đối chiếu bảng dung sai kích thước và tiêu chuẩn ngoại quan ISO 9001.")


safety_gate = QCSafetyGate()
