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
        max_total_area_ratio: float = 0.03,  # Defect area ratio > 3% triggers QUARANTINE
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
        negligible_count = sum(1 for d in valid_defects if d.severity == DefectSeverity.NEGLIGIBLE)
        total_area = sum(d.area_ratio for d in valid_defects)

        rule_evals["critical_count"] = critical_count
        rule_evals["major_count"] = major_count
        rule_evals["minor_count"] = minor_count
        rule_evals["negligible_count"] = negligible_count
        rule_evals["total_area_ratio"] = round(total_area, 4)
        rule_evals["area_threshold"] = self.config.max_total_area_ratio

        # Rule 1: Zero Critical Defect Tolerance -> Auto-Quarantine (crack, structural porosity)
        if critical_count > self.config.max_critical_defects:
            verdict = QualityVerdict.QUARANTINE
            reasons.append(
                f"CRITICAL DEFECT DETECTED: Found {critical_count} critical defects (Max allowed: {self.config.max_critical_defects}). Immediate quarantine required."
            )
            return verdict, reasons, rule_evals

        # Rule 2: Total Defect Area Ratio > 3% -> Auto-Quarantine for physical evaluation
        if total_area > self.config.max_total_area_ratio:
            verdict = QualityVerdict.QUARANTINE
            reasons.append(
                f"DEFECT AREA LIMIT EXCEEDED: Defect area ratio is {total_area:.2%} (Threshold: {self.config.max_total_area_ratio:.2%}). Quarantine required for physical inspection."
            )
            return verdict, reasons, rule_evals

        # Rule 3: Major Defect Tolerance Exceeded -> Quarantine
        if major_count > self.config.max_major_defects:
            verdict = QualityVerdict.QUARANTINE
            reasons.append(
                f"MAJOR DEFECT COUNT EXCEEDED: Found {major_count} major defects (Max allowed: {self.config.max_major_defects}). Quarantine required."
            )
            return verdict, reasons, rule_evals

        # Rule 4: Color/minor defects below threshold trigger PASSED
        verdict = QualityVerdict.PASSED
        reasons.append(
            f"Quality inspection criteria met. No critical defects; defect area ratio ({total_area:.2%}) is within tolerance (<= {self.config.max_total_area_ratio:.2%}); minor surface imperfections within allowable limits."
        )
        return verdict, reasons, rule_evals


rules_engine = QCRulesEngine()
