# PROJECT 2: Visual Quality Gate (Manufacturing Defect Inspection)

## 1. Overview
Visual Quality Gate is an edge-optimized industrial computer vision inspection engine. It processes manufacturing part images, detects defects via ONNX Runtime CPU inference, applies deterministic safety rules, and synchronizes records directly into ERPNext `Quality Inspection`.

## 2. Key Technical Capabilities
- **ONNX Runtime CPU Inference**: Quantized YOLOv8 defect detection model operating with bounded OpenMP threads (`OMP_NUM_THREADS=2`), achieving median latency of 71.2ms on ARM64 CPU.
- **Deterministic Safety Gate**: Isolates the LLM from safety-critical decisions. Defect area calculations and severity counts strictly determine `PASSED`, `QUARANTINE`, or `REJECTED` verdicts.
- **Redpanda / Kafka 8-Event Lifecycle Stream**: Implements strict schemas and correlation IDs for:
  1. `inspection.created`
  2. `inspection.image.uploaded`
  3. `inspection.inference.completed`
  4. `inspection.review.completed`
  5. `inspection.quality.decided`
  6. `inspection.erp.sync.requested`
  7. `inspection.erp.sync.completed`
  8. `inspection.erp.sync.failed`
- **ERPNext Synchronization**: Idempotent synchronization creating and updating `Quality Inspection` DocTypes.
