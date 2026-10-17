# Inspection Sample Dataset

This directory contains verified sample inspection images for testing Project 2 (Visual Quality Gate).

| File Name | Description | Expected Decision | Reason / Rule Trigger |
| :--- | :--- | :---: | :--- |
| `sample_normal_plate.jpg` | Clean machined aerospace aluminum CNC plate (ALU-CNC-001) | **PASSED** | Defect-free / within visual tolerances |
| `sample_surface_crack.jpg` | Aluminum plate with continuous fracture along center axis | **QUARANTINE** | Critical defect detected: `surface_crack` (Class 0) |
| `sample_structural_porosity.jpg` | Cast plate with clustered gas void micro-porosity | **QUARANTINE** | Critical structural porosity defect: `structural_porosity` (Class 4) |

### Test Ingestion via cURL:
```bash
curl -X POST "http://localhost:8002/api/qc/v1/inspections" \
  -H "Authorization: Bearer mock-token-inspector" \
  -F "file=@data/inspection-samples/sample_surface_crack.jpg" \
  -F "item_code=ALU-CNC-001" \
  -F "batch_number=BATCH-2026-X1" \
  -F "work_order_id=WO-90812"
```
