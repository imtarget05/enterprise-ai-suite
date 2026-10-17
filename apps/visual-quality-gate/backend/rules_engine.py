"""
Deterministic QC Rules Engine for Product B.
Evaluates detected defects against strict industrial tolerance thresholds.
Decides Quality Verdict: PASSED, QUARANTINE, or REJECTED.
"""

from typing import Any, Dict, List, Tuple
from packages.shared_contracts.events import BoundingBox, DefectSeverity, QualityVerdict


class QCRulesConfig:
    def __init__(
        self,
        max_critical_defects: int = 0,
        max_major_defects: int = 1,
        max_total_area_ratio: float = 0.04,  # Defect area cannot exceed 4% of surface
        min_confidence_to_flag: float = 0.40,
    ):
        self.max_critical_defects = max_critical_defects
        self.max_major_defects = max_major_defects
        self.max_total_area_ratio = max_total_area_ratio
        self.min_confidence_to_flag = min_confidence_to_flag


class QCRulesEngine:
    def __init__(self, config: QCRulesConfig = QCRulesConfig()):
        self.config = config

    def evaluate(self, defects: List[BoundingBox]) -> Tuple[QualityVerdict, List[str], Dict[str, Any]]:
        reasons = []
        rule_evals = {}

        # 1. Filter by minimum confidence
        valid_defects = [d for d in defects if d.confidence >= self.config.min_confidence_to_flag]
        
        # 2. Count defects by severity
        critical_count = sum(1 for d in valid_defects if d.severity == DefectSeverity.CRITICAL)
        major_count = sum(1 for d in valid_defects if d.severity == DefectSeverity.MAJOR)
        minor_count = sum(1 for d in valid_defects if d.severity == DefectSeverity.MINOR)
        total_area = sum(d.area_ratio for d in valid_defects)

        rule_evals["critical_count"] = critical_count
        rule_evals["major_count"] = major_count
        rule_evals["minor_count"] = minor_count
        rule_evals["total_area_ratio"] = round(total_area, 4)

        # Rule 1: Zero Critical Defect Tolerance -> Auto-Quarantine for physical inspection
        if critical_count > self.config.max_critical_defects:
            verdict = QualityVerdict.QUARANTINE
            reasons.append(f"CRITICAL DEFECT DETECTED: Found {critical_count} critical defects (Max allowed: 0). Immediate quarantine required.")
            return verdict, reasons, rule_evals

        # Rule 2: Excessive Total Defect Area -> Outright Reject
        if total_area > self.config.max_total_area_ratio:
            verdict = QualityVerdict.REJECTED
            reasons.append(f"SURFACE AREA LIMIT EXCEEDED: Defect area ratio is {total_area:.2%} (Max allowed: {self.config.max_total_area_ratio:.2%}).")
            return verdict, reasons, rule_evals

        # Rule 3: Major Defect Tolerance Exceeded
        if major_count > self.config.max_major_defects:
            verdict = QualityVerdict.REJECTED
            reasons.append(f"MAJOR DEFECT COUNT EXCEEDED: Found {major_count} major defects (Max allowed: {self.config.max_major_defects}).")
            return verdict, reasons, rule_evals

        # If only minor/negligible defects within tolerance
        verdict = QualityVerdict.PASSED
        reasons.append("Quality inspection criteria met. No critical defects; minor surface imperfections within tolerance.")
        return verdict, reasons, rule_evals


rules_engine = QCRulesEngine()
