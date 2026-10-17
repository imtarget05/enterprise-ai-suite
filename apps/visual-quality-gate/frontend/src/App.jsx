import React, { useState, useEffect, useRef } from 'react';

const SEVERITY_COLORS = {
  CRITICAL: {
    stroke: '#EF4444',
    fill: 'rgba(239, 68, 68, 0.25)',
    glow: 'rgba(239, 68, 68, 0.7)',
    badgeBg: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
    tag: 'bg-rose-600 text-white',
  },
  MAJOR: {
    stroke: '#F97316',
    fill: 'rgba(249, 115, 22, 0.25)',
    glow: 'rgba(249, 115, 22, 0.7)',
    badgeBg: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
    tag: 'bg-orange-600 text-white',
  },
  MINOR: {
    stroke: '#EAB308',
    fill: 'rgba(234, 179, 8, 0.25)',
    glow: 'rgba(234, 179, 8, 0.7)',
    badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    tag: 'bg-amber-500 text-slate-950',
  },
  NEGLIGIBLE: {
    stroke: '#3B82F6',
    fill: 'rgba(59, 130, 246, 0.22)',
    glow: 'rgba(59, 130, 246, 0.7)',
    badgeBg: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
    tag: 'bg-blue-600 text-white',
  },
};

const SOP_CATALOG = {
  surface_crack: 'SOP-QC-CRACK-01: Vết nứt bề mặt có nguy cơ nứt gãy cơ học. Cách ly chi tiết vào khay đỏ (Red Bin), gắn thẻ Quarantine, chuyển ảnh qua phòng Lab NDT thẩm định.',
  structural_porosity: 'SOP-QC-POROSITY-02: Độ xốp / rỗ khí kết cấu (structural porosity) làm giảm độ bền mỏi. Cách ly chi tiết vào khu vực Red Bin và kiểm tra chụp X-quang công nghiệp (CT scan).',
  void_cavity: 'SOP-QC-VOID-02: Rỗ khí đúc vượt tiêu chuẩn yêu cầu kiểm tra siêu âm NDT (Non-Destructive Testing) để xác định độ sâu khuyết tật.',
  dent_scratch: 'SOP-QC-SCRATCH-03: Vết trầy xước nhẹ có thể xử lý đánh bóng lại (Rework) nếu chiều sâu < 0.2mm.',
  color_defect: 'SOP-QC-COLOR-04: Sai lệch màu Anodize chấp nhận được nếu Delta E < 2.0 theo tiêu chuẩn ngoại quan ISO 9001.',
};

export default function App() {
  const [inspection, setInspection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [sopInfo, setSopInfo] = useState('');
  const [selectedDefect, setSelectedDefect] = useState(null);
  const [hoveredDefect, setHoveredDefect] = useState(null);
  const [apiStatus, setApiStatus] = useState('Checking...');
  const [erpSynced, setErpSynced] = useState(false);
  const [erpLoading, setErpLoading] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideVerdict, setOverrideVerdict] = useState('PASSED');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideCertified, setOverrideCertified] = useState(false);
  const [overrideNotice, setOverrideNotice] = useState(null);

  const canvasRef = useRef(null);
  const API_BASE = import.meta.env.VITE_QC_API_BASE_URL || 'http://localhost:8002/api/qc';

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((d) => setApiStatus(d.status === 'healthy' ? 'Online' : d.status))
      .catch(() => setApiStatus('Offline (Local Engine)'));
  }, [API_BASE]);

  // Initial load of sample inspection
  useEffect(() => {
    loadInspectionPreset('critical_crack');
  }, []);

  // Redraw Canvas whenever inspection, selectedDefect, or hoveredDefect changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // 1. Draw High-Fidelity Industrial CNC Part Background
    ctx.clearRect(0, 0, width, height);

    // Workbench background
    ctx.fillStyle = '#090d16';
    ctx.fillRect(0, 0, width, height);

    // Grid coordinates
    ctx.strokeStyle = 'rgba(51, 65, 85, 0.25)';
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Machined Aluminum Billet Plate
    const plateMargin = 60;
    const pW = width - plateMargin * 2;
    const pH = height - plateMargin * 2;

    const grad = ctx.createLinearGradient(plateMargin, plateMargin, width - plateMargin, height - plateMargin);
    grad.addColorStop(0, '#334155');
    grad.addColorStop(0.5, '#1e293b');
    grad.addColorStop(1, '#0f172a');

    ctx.fillStyle = grad;
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 3;

    // Rounded rectangle plate
    const r = 24;
    ctx.beginPath();
    ctx.moveTo(plateMargin + r, plateMargin);
    ctx.lineTo(plateMargin + pW - r, plateMargin);
    ctx.quadraticCurveTo(plateMargin + pW, plateMargin, plateMargin + pW, plateMargin + r);
    ctx.lineTo(plateMargin + pW, plateMargin + pH - r);
    ctx.quadraticCurveTo(plateMargin + pW, plateMargin + pH, plateMargin + pW - r, plateMargin + pH);
    ctx.lineTo(plateMargin + r, plateMargin + pH);
    ctx.quadraticCurveTo(plateMargin, plateMargin + pH, plateMargin, plateMargin + pH - r);
    ctx.lineTo(plateMargin, plateMargin + r);
    ctx.quadraticCurveTo(plateMargin, plateMargin, plateMargin + r, plateMargin);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Four Mounting Holes
    const holes = [
      [plateMargin + 32, plateMargin + 32],
      [width - plateMargin - 32, plateMargin + 32],
      [plateMargin + 32, height - plateMargin - 32],
      [width - plateMargin - 32, height - plateMargin - 32],
    ];
    holes.forEach(([hx, hy]) => {
      ctx.beginPath();
      ctx.arc(hx, hy, 14, 0, Math.PI * 2);
      ctx.fillStyle = '#020617';
      ctx.fill();
      ctx.strokeStyle = '#94a3b8';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(hx, hy, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#0f172a';
      ctx.fill();
    });

    // Concentric Machining Milling Grooves
    const cx = width / 2;
    const cy = height / 2;
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.18)';
    ctx.setLineDash([4, 4]);
    [60, 100, 140, 180].forEach((radius) => {
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.stroke();
    });
    ctx.setLineDash([]);

    // Center Borehole
    ctx.beginPath();
    ctx.arc(cx, cy, 40, 0, Math.PI * 2);
    ctx.fillStyle = '#020617';
    ctx.fill();
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 4;
    ctx.stroke();

    // Optical Target Crosshairs
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - 55, cy);
    ctx.lineTo(cx + 55, cy);
    ctx.moveTo(cx, cy - 55);
    ctx.lineTo(cx, cy + 55);
    ctx.stroke();

    // Stamped Identification
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px monospace';
    ctx.fillText('ALU-CNC-001 | 2026-X1 | MIL-STD-1520C', plateMargin + 16, height - plateMargin - 16);

    // 2. Draw Defect Bounding Boxes with Color-Coded Severity
    if (inspection && inspection.defects) {
      inspection.defects.forEach((d, idx) => {
        const x = d.x_min * width;
        const y = d.y_min * height;
        const w = (d.x_max - d.x_min) * width;
        const h = (d.y_max - d.y_min) * height;

        const sev = d.severity || 'MINOR';
        const colorCfg = SEVERITY_COLORS[sev] || SEVERITY_COLORS.MINOR;
        const isSelected = selectedDefect && selectedDefect.idx === idx;
        const isHovered = hoveredDefect && hoveredDefect.idx === idx;

        // Shadow / Glow
        ctx.save();
        ctx.shadowColor = colorCfg.glow;
        ctx.shadowBlur = isSelected ? 16 : isHovered ? 10 : 4;

        // Box Fill
        ctx.fillStyle = isSelected ? colorCfg.fill.replace('0.25', '0.45') : colorCfg.fill;
        ctx.fillRect(x, y, w, h);

        // Box Border
        ctx.strokeStyle = colorCfg.stroke;
        ctx.lineWidth = isSelected ? 3.5 : 2;
        ctx.strokeRect(x, y, w, h);

        // Corner targeting brackets
        const bLen = Math.min(10, w / 3, h / 3);
        ctx.lineWidth = isSelected ? 4 : 3;
        ctx.beginPath();
        // Top-left
        ctx.moveTo(x, y + bLen); ctx.lineTo(x, y); ctx.lineTo(x + bLen, y);
        // Top-right
        ctx.moveTo(x + w - bLen, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + bLen);
        // Bottom-right
        ctx.moveTo(x + w, y + h - bLen); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - bLen, y + h);
        // Bottom-left
        ctx.moveTo(x + bLen, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + h - bLen);
        ctx.stroke();

        ctx.restore();

        // Defect Label Badge
        const labelText = `${d.class_name} [${sev}] ${(d.confidence * 100).toFixed(0)}%`;
        ctx.font = 'bold 11px monospace';
        const textWidth = ctx.measureText(labelText).width;
        const badgeH = 18;
        const badgeY = y > 24 ? y - badgeH - 3 : y + h + 3;

        ctx.fillStyle = '#0f172a';
        ctx.fillRect(x, badgeY, textWidth + 12, badgeH);
        ctx.strokeStyle = colorCfg.stroke;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, badgeY, textWidth + 12, badgeH);

        ctx.fillStyle = colorCfg.stroke;
        ctx.fillText(labelText, x + 6, badgeY + 13);
      });
    }
  }, [inspection, selectedDefect, hoveredDefect]);

  // Handle Canvas Mouse Move (hit test bounding boxes)
  const handleCanvasMouseMove = (e) => {
    if (!canvasRef.current || !inspection || !inspection.defects) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const clickX = (e.clientX - rect.left) * scaleX;
    const clickY = (e.clientY - rect.top) * scaleY;

    const normX = clickX / canvasRef.current.width;
    const normY = clickY / canvasRef.current.height;

    let hit = null;
    inspection.defects.forEach((d, idx) => {
      if (normX >= d.x_min && normX <= d.x_max && normY >= d.y_min && normY <= d.y_max) {
        hit = { ...d, idx };
      }
    });

    setHoveredDefect(hit);
    canvasRef.current.style.cursor = hit ? 'pointer' : 'crosshair';
  };

  // Handle Canvas Click to select defect
  const handleCanvasClick = (e) => {
    if (hoveredDefect) {
      handleSelectDefect(hoveredDefect);
    } else {
      setSelectedDefect(null);
    }
  };

  const handleSelectDefect = (defectWithIdx) => {
    setSelectedDefect(defectWithIdx);
    const sop = SOP_CATALOG[defectWithIdx.class_name] || 'SOP-QC-GENERIC: Kiểm tra đối chiếu bảng dung sai kích thước và tiêu chuẩn ngoại quan ISO 9001.';
    setSopInfo(sop);
  };

  // Load Inspection Presets to test edge cases
  const loadInspectionPreset = (presetKey) => {
    setLoading(true);
    setErpSynced(false);
    setSelectedDefect(null);
    setOverrideNotice(null);

    setTimeout(() => {
      const inspId = `INSP-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      const corrId = `corr-${Math.random().toString(36).substring(2, 10)}`;

      let boxes = [];
      let verdict = 'PASSED';
      let reasons = [];

      if (presetKey === 'critical_crack') {
        boxes = [
          {
            class_id: 0,
            class_name: 'surface_crack',
            confidence: 0.91,
            severity: 'CRITICAL',
            x_min: 0.28,
            y_min: 0.35,
            x_max: 0.48,
            y_max: 0.58,
            area_ratio: 0.046,
          },
          {
            class_id: 2,
            class_name: 'dent_scratch',
            confidence: 0.74,
            severity: 'MINOR',
            x_min: 0.65,
            y_min: 0.20,
            x_max: 0.78,
            y_max: 0.32,
            area_ratio: 0.015,
          },
        ];
        verdict = 'QUARANTINE';
        reasons = [
          'CRITICAL DEFECT DETECTED: Phát hiện 1 vết nứt bề mặt (surface_crack). Yêu cầu cách ly lập tức (Zero-tolerance).',
          'DEFECT AREA LIMIT EXCEEDED: Tổng diện tích lỗi 6.10% vượt ngưỡng 3.00%.',
        ];
      } else if (presetKey === 'structural_porosity') {
        boxes = [
          {
            class_id: 4,
            class_name: 'structural_porosity',
            confidence: 0.88,
            severity: 'CRITICAL',
            x_min: 0.38,
            y_min: 0.38,
            x_max: 0.46,
            y_max: 0.46,
            area_ratio: 0.0064,
          },
        ];
        verdict = 'QUARANTINE';
        reasons = [
          'CRITICAL DEFECT DETECTED: Phát hiện rỗ khí kết cấu (structural_porosity). Nguy cơ gãy mỏi chịu lực, cách ly chuyển kiểm tra CT scan.',
        ];
      } else if (presetKey === 'area_exceeded') {
        boxes = [
          {
            class_id: 2,
            class_name: 'dent_scratch',
            confidence: 0.76,
            severity: 'MINOR',
            x_min: 0.15,
            y_min: 0.18,
            x_max: 0.35,
            y_max: 0.32,
            area_ratio: 0.028,
          },
          {
            class_id: 2,
            class_name: 'dent_scratch',
            confidence: 0.69,
            severity: 'MINOR',
            x_min: 0.55,
            y_min: 0.52,
            x_max: 0.68,
            y_max: 0.65,
            area_ratio: 0.0169,
          },
        ];
        verdict = 'QUARANTINE';
        reasons = [
          'DEFECT AREA LIMIT EXCEEDED: Tổng tỷ lệ diện tích lỗi là 4.49% (Ngưỡng cho phép: 3.00%). Cách ly chờ đánh bóng / rework.',
        ];
      } else {
        // Standard pass
        boxes = [
          {
            class_id: 3,
            class_name: 'color_defect',
            confidence: 0.62,
            severity: 'NEGLIGIBLE',
            x_min: 0.12,
            y_min: 0.12,
            x_max: 0.18,
            y_max: 0.18,
            area_ratio: 0.0036,
          },
        ];
        verdict = 'PASSED';
        reasons = [
          'Quality inspection criteria met. Không có lỗi trọng yếu (0 critical); tỷ lệ diện tích lỗi 0.36% nằm trong giới hạn cho phép (<= 3.00%).',
        ];
      }

      setInspection({
        id: inspId,
        correlation_id: corrId,
        item_code: 'ALU-CNC-001',
        batch_number: 'BATCH-2026-X1',
        latency_ms: 68.4,
        defects: boxes,
        verdict: verdict,
        reasons: reasons,
        model_version: 'yolov8n-defect-v1.2-quantized',
      });

      // Populate initial Redpanda 8-event stream (Events 1-4)
      const now = new Date().toISOString().substring(11, 23);
      setEvents([
        {
          seq: 1,
          type: 'inspection.created',
          ts: now,
          key: inspId,
          corrId,
          idempKey: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          status: 'OK',
          detail: 'Part ALU-CNC-001 queued at Line 01',
        },
        {
          seq: 2,
          type: 'inspection.image.uploaded',
          ts: now,
          key: inspId,
          corrId,
          idempKey: '8f3d6b20a174c8901e4d36e2f1e29c67bc250917281f62b2e88a09b30c149d8a',
          status: 'OK (R2 Store)',
          detail: 'Stored: inspections/640x640_part.jpg (SHA-256 verified)',
        },
        {
          seq: 3,
          type: 'inspection.inference.completed',
          ts: now,
          key: inspId,
          corrId,
          idempKey: 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
          status: 'OK (68.4 ms)',
          detail: `ONNX CPU Infer: ${boxes.length} defects detected (< 80ms target)`,
        },
        {
          seq: 4,
          type: 'inspection.quality.decided',
          ts: now,
          key: inspId,
          corrId,
          idempKey: '1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c',
          status: `VERDICT: ${verdict}`,
          detail: `Deterministic Safety Gate: ${verdict} (Zero LLM Involvement)`,
        },
      ]);

      if (boxes.length > 0) {
        handleSelectDefect({ ...boxes[0], idx: 0 });
      }

      setLoading(false);
    }, 350);
  };

  // Sync to ERPNext (Triggers Events 6 & 7, or 8)
  const handleSyncERP = async (simulateFailure = false) => {
    if (!inspection) return;
    setErpLoading(true);

    const now = new Date().toISOString().substring(11, 23);
    const corrId = inspection.correlation_id;

    // Event 6: ERP Sync Requested
    setEvents((prev) => [
      ...prev,
      {
        seq: prev.length + 1,
        type: 'inspection.erp.sync.requested',
        ts: now,
        key: inspection.id,
        corrId,
        idempKey: 'c0a80101b4c8996fb92427ae41e4649b934ca495991b7852b855e3b0c44298fc',
        status: 'DISPATCHED',
        detail: `Item: ${inspection.item_code} | Batch: ${inspection.batch_number} | Verdict: ${inspection.verdict}`,
      },
    ]);

    setTimeout(() => {
      const now2 = new Date().toISOString().substring(11, 23);
      if (simulateFailure) {
        // Event 8: ERP Sync Failed
        setEvents((prev) => [
          ...prev,
          {
            seq: prev.length + 1,
            type: 'inspection.erp.sync.failed',
            ts: now2,
            key: inspection.id,
            corrId,
            idempKey: 'f4b3a2e1d0c9b8a7f6e5d4c3b2a10987654321fedcba0987654321abcdef0123',
            status: 'FAILED (HTTP 503)',
            detail: 'ERPNext Gateway Timeout. Retrying via outbox worker...',
          },
        ]);
        setErpLoading(false);
      } else {
        // Event 7: ERP Sync Completed
        const docName = `QI-2026-0${Math.floor(100 + Math.random() * 900)}`;
        setEvents((prev) => [
          ...prev,
          {
            seq: prev.length + 1,
            type: 'inspection.erp.sync.completed',
            ts: now2,
            key: inspection.id,
            corrId,
            idempKey: '7c4a8d09ca3762af61e59520943dc26494f8941b',
            status: `DOC: ${docName}`,
            detail: `ERPNext Quality Inspection created with ${inspection.defects.length} readings recorded.`,
          },
        ]);
        setErpSynced(true);
        setErpLoading(false);
      }
    }, 500);
  };

  // Submit Manual Inspector Override (Event 5)
  const handleSubmitOverride = () => {
    if (!overrideReason || overrideReason.trim().length < 10) return;

    const now = new Date().toISOString().substring(11, 23);
    const corrId = inspection.correlation_id;

    // Event 5: Review Completed
    setEvents((prev) => [
      ...prev,
      {
        seq: prev.length + 1,
        type: 'inspection.review.completed',
        ts: now,
        key: inspection.id,
        corrId,
        idempKey: '9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d',
        status: `OVERRIDDEN TO: ${overrideVerdict}`,
        detail: `Reviewer: QC-INSP-007 | Action: OVERRIDE | Reason: ${overrideReason}`,
      },
    ]);

    setOverrideNotice({
      reviewer: 'QC-INSP-007 (Lead Inspector)',
      originalVerdict: inspection.verdict,
      newVerdict: overrideVerdict,
      reason: overrideReason,
      timestamp: now,
    });

    setInspection((prev) => ({
      ...prev,
      verdict: overrideVerdict,
    }));

    setShowOverrideModal(false);
    setOverrideReason('');
    setOverrideCertified(false);
  };

  return (
    <div className="flex flex-col h-screen max-w-7xl mx-auto p-4 font-sans text-slate-100 bg-slate-950">
      {/* Header */}
      <header className="flex justify-between items-center pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🔍</span>
            <h1 className="text-xl font-bold tracking-tight text-amber-400">
              Visual Quality Gate & Defect Inspection (Product B)
            </h1>
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-amber-400/10 text-amber-300 border border-amber-400/30">
              v1.2.0
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            YOLOv8 Quantized ONNX CPU Inference · Deterministic Safety Gate · Redpanda 8-Event Stream · ERPNext QI Sync
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className={`w-2.5 h-2.5 rounded-full ${apiStatus === 'Online' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
            <span>API: <strong className="text-emerald-400">{apiStatus}</strong></span>
          </div>
          <div className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 font-mono text-[11px]">
            Engine: <strong className="text-sky-300">ONNX CPU (2 Threads)</strong>
          </div>
        </div>
      </header>

      {/* Main Grid: 7 cols Canvas + Defect Table / 5 cols Status & Audit Stream */}
      <div className="flex-1 grid grid-cols-12 gap-4 mt-3 overflow-hidden">
        {/* Left Column (7 cols): Canvas & Defect Table */}
        <div className="col-span-7 flex flex-col gap-3 overflow-hidden">
          {/* Canvas Card */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-3 flex flex-col flex-1 overflow-hidden">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <span>🖼️</span> Interactive HTML5 Canvas (640x640 Sensor View)
              </span>
              <div className="flex gap-1.5">
                <button
                  onClick={() => loadInspectionPreset('critical_crack')}
                  className="px-2.5 py-1 bg-rose-950/80 hover:bg-rose-900 border border-rose-600/60 text-rose-200 text-[11px] font-semibold rounded transition"
                >
                  ⚡ Crack (Quarantine)
                </button>
                <button
                  onClick={() => loadInspectionPreset('structural_porosity')}
                  className="px-2.5 py-1 bg-red-950/80 hover:bg-red-900 border border-red-500/60 text-red-200 text-[11px] font-semibold rounded transition"
                >
                  🔘 Porosity (Quarantine)
                </button>
                <button
                  onClick={() => loadInspectionPreset('area_exceeded')}
                  className="px-2.5 py-1 bg-orange-950/80 hover:bg-orange-900 border border-orange-500/60 text-orange-200 text-[11px] font-semibold rounded transition"
                >
                  📊 Area &gt; 3%
                </button>
                <button
                  onClick={() => loadInspectionPreset('pass_clean')}
                  className="px-2.5 py-1 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-500/60 text-emerald-200 text-[11px] font-semibold rounded transition"
                >
                  ✓ Pass
                </button>
              </div>
            </div>

            {/* Canvas Viewport */}
            <div className="flex-1 relative mt-2 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center overflow-hidden">
              <canvas
                ref={canvasRef}
                width={640}
                height={640}
                onMouseMove={handleCanvasMouseMove}
                onClick={handleCanvasClick}
                className="max-h-full max-w-full object-contain cursor-crosshair rounded"
              />
              {loading && (
                <div className="absolute inset-0 bg-slate-950/85 flex flex-col items-center justify-center text-xs text-amber-400 gap-2">
                  <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
                  <span className="font-mono">ONNX CPU Quantized Forward Pass (OMP_NUM_THREADS=2)...</span>
                </div>
              )}
            </div>

            {/* Canvas Telemetry Footer */}
            <div className="mt-2 pt-2 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400 font-mono">
              <span>SLA Latency: <strong className="text-emerald-400">{inspection ? `${inspection.latency_ms} ms` : '--'}</strong> (SLA &lt; 200ms)</span>
              <span>Model: <strong className="text-sky-300">YOLOv8n-INT8</strong></span>
              <span>Resolution: <strong className="text-slate-300">1920x1080 &rarr; 640x640</strong></span>
            </div>
          </div>

          {/* Defect Classification Table Card */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-3 h-48 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center pb-1.5 border-b border-slate-800">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                📋 Defect Classification & Tolerance Table
              </h3>
              <span className="text-[10px] text-slate-400">
                {inspection?.defects?.length || 0} defects identified
              </span>
            </div>
            <div className="flex-1 overflow-y-auto mt-1">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                    <th className="pb-1.5 font-semibold">Defect Class</th>
                    <th className="pb-1.5 font-semibold">Severity Tag</th>
                    <th className="pb-1.5 font-semibold">Confidence</th>
                    <th className="pb-1.5 font-semibold">Area Ratio</th>
                    <th className="pb-1.5 font-semibold text-right">Advisory SOP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {inspection?.defects && inspection.defects.length > 0 ? (
                    inspection.defects.map((d, i) => {
                      const colorCfg = SEVERITY_COLORS[d.severity] || SEVERITY_COLORS.MINOR;
                      const isSelected = selectedDefect && selectedDefect.idx === i;
                      return (
                        <tr
                          key={i}
                          onClick={() => handleSelectDefect({ ...d, idx: i })}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? 'bg-slate-800/90 text-white' : 'hover:bg-slate-800/40 text-slate-300'
                          }`}
                        >
                          <td className="py-1.5 font-bold flex items-center gap-1.5">
                            <span
                              className="w-2 h-2 rounded-full inline-block"
                              style={{ backgroundColor: colorCfg.stroke }}
                            ></span>
                            {d.class_name}
                          </td>
                          <td className="py-1.5">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${colorCfg.badgeBg}`}
                            >
                              {d.severity}
                            </span>
                          </td>
                          <td className="py-1.5 text-slate-200">
                            {(d.confidence * 100).toFixed(1)}%
                          </td>
                          <td className="py-1.5">
                            <span
                              className={`px-1 rounded text-[11px] ${
                                d.area_ratio > 0.03
                                  ? 'text-rose-400 font-bold bg-rose-950/60'
                                  : 'text-slate-300'
                              }`}
                            >
                              {(d.area_ratio * 100).toFixed(2)}%
                              {d.area_ratio > 0.03 && ' (Exceeds 3%)'}
                            </span>
                          </td>
                          <td className="py-1.5 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSelectDefect({ ...d, idx: i });
                              }}
                              className="text-[10px] px-2 py-0.5 rounded bg-sky-950 hover:bg-sky-900 text-sky-300 border border-sky-800"
                            >
                              View SOP &rarr;
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="5" className="py-4 text-center text-slate-500 italic">
                        ✓ No defects detected. Billet surface within allowable ISO-9001 tolerance.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Status Card, SOP, Redpanda Events */}
        <div className="col-span-5 flex flex-col gap-3 overflow-hidden">
          {/* Deterministic Safety Gate Status Card */}
          <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-2.5">
            <div className="flex justify-between items-center">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Deterministic Safety Gate Decision
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono border border-slate-700">
                100% Rule-Based · Zero LLM
              </span>
            </div>

            {/* Verdict Badge */}
            <div className="flex items-center justify-between bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <div>
                <span className="text-[11px] text-slate-400 block font-mono">
                  Mã phiếu: <strong>{inspection?.id || '--'}</strong>
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  Chi tiết: <strong className="text-slate-200">{inspection?.item_code}</strong>
                </span>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span
                  className={`px-3 py-1 rounded text-xs font-black tracking-wide border ${
                    inspection?.verdict === 'PASSED'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 shadow-lg shadow-emerald-950'
                      : inspection?.verdict === 'QUARANTINE'
                      ? 'bg-amber-500/20 text-amber-400 border-amber-500/50 shadow-lg shadow-amber-950'
                      : 'bg-rose-500/20 text-rose-400 border-rose-500/50 shadow-lg shadow-rose-950'
                  }`}
                >
                  {inspection?.verdict === 'PASSED' ? '✓ PASSED' : '🛡️ QUARANTINE'}
                </span>
                {overrideNotice && (
                  <span className="text-[9px] text-sky-400 font-bold uppercase tracking-tight">
                    [Overridden by Inspector]
                  </span>
                )}
              </div>
            </div>

            {/* Decision Rule Explanations */}
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-300 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Rule Evaluations:</span>
              {inspection?.reasons?.map((r, i) => (
                <p key={i} className="text-slate-300 flex items-start gap-1.5 leading-snug">
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{r}</span>
                </p>
              ))}
            </div>

            {/* Override Banner if active */}
            {overrideNotice && (
              <div className="bg-sky-950/60 p-2 rounded-lg border border-sky-600/50 text-[11px] text-sky-200 space-y-0.5">
                <div className="font-bold flex justify-between">
                  <span>Inspector Override Active</span>
                  <span className="font-mono text-[10px]">{overrideNotice.timestamp}</span>
                </div>
                <p className="text-[10px] text-slate-300 italic">"{overrideNotice.reason}"</p>
              </div>
            )}

            {/* Action Buttons: Override & ERPNext Sync */}
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => setShowOverrideModal(true)}
                className="px-3 py-2 rounded text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              >
                ⚙️ Manual Override
              </button>
              <button
                disabled={erpSynced || erpLoading}
                onClick={() => handleSyncERP(false)}
                className={`flex-1 py-2 rounded text-xs font-semibold transition ${
                  erpSynced
                    ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-600/40 cursor-default'
                    : 'bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow'
                }`}
              >
                {erpLoading
                  ? 'Connecting to ERP...'
                  : erpSynced
                  ? '✓ Synced to ERPNext QI'
                  : '📤 Sync to ERPNext (QI)'}
              </button>
            </div>
          </div>

          {/* SOP Advisory Card */}
          {sopInfo && (
            <div className="bg-slate-900 p-3 rounded-xl border border-sky-500/40 text-xs space-y-1">
              <div className="text-sky-400 font-bold uppercase flex items-center gap-1.5 text-[11px]">
                <span>💡</span> Advisory SOP Instruction:
              </div>
              <p className="text-slate-200 text-[11px] leading-relaxed">{sopInfo}</p>
            </div>
          )}

          {/* Live 8-Event Redpanda Lifecycle Audit Viewer */}
          <div className="flex-1 bg-slate-900 p-3.5 rounded-xl border border-slate-800 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <div className="flex items-center gap-1.5">
                <span className="text-sm">📡</span>
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                  Redpanda 8-Event Lifecycle Audit
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-emerald-400 font-mono">
                  enterprise.qc.inspections
                </span>
                <button
                  onClick={() => handleSyncERP(true)}
                  title="Simulate transient network timeout and DLQ retry event"
                  className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700"
                >
                  Test Fail/Retry
                </button>
              </div>
            </div>

            {/* Events List */}
            <div className="flex-1 mt-2 overflow-y-auto space-y-1.5 font-mono text-[11px] pr-1">
              {events.length > 0 ? (
                events.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-bold">
                          #{ev.seq}
                        </span>
                        <span className="text-amber-400 font-bold text-xs">{ev.type}</span>
                      </div>
                      <span className="text-[10px] text-emerald-400 font-semibold">{ev.status}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
                      <span>Partition: <strong className="text-slate-300">{ev.key}</strong></span>
                      <span className="text-slate-500">{ev.ts}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 truncate mt-0.5">
                      IdempKey: <span className="text-slate-400">{ev.idempKey}</span>
                    </div>
                    {ev.detail && (
                      <div className="text-[10px] text-slate-300 mt-1 pt-1 border-t border-slate-900 italic">
                        {ev.detail}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-slate-600 text-xs italic py-4 text-center">
                  Chưa có sự kiện nào trong luồng Redpanda.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Manual Inspector Override Modal with Mandatory Audit Reason */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-5 shadow-2xl flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-amber-400 flex items-center gap-2">
                <span>🛡️</span> Manual Inspector Override & Audit Record
              </h3>
              <button
                onClick={() => setShowOverrideModal(false)}
                className="text-slate-400 hover:text-white text-base"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block font-semibold mb-1">
                  Current Automated Decision:
                </label>
                <div className="px-3 py-1.5 bg-slate-950 rounded border border-slate-800 font-mono text-amber-300">
                  {inspection?.verdict} (Deterministic Safety Gate)
                </div>
              </div>

              <div>
                <label className="text-slate-400 block font-semibold mb-1">
                  Target Override Verdict:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['PASSED', 'QUARANTINE', 'REJECTED'].map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => setOverrideVerdict(v)}
                      className={`py-2 rounded font-bold border transition ${
                        overrideVerdict === v
                          ? 'bg-amber-400 text-slate-950 border-amber-300'
                          : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-slate-400 block font-semibold mb-1">
                  Inspector Credential / Badge ID:
                </label>
                <input
                  type="text"
                  readOnly
                  value="QC-INSP-007 (Lead Inspector - QA Division)"
                  className="w-full px-3 py-1.5 bg-slate-950 rounded border border-slate-800 font-mono text-slate-300 text-xs"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-rose-400 font-semibold flex items-center gap-1">
                    <span>*</span> Mandatory Audit Reason (ISO-9001 Compliance):
                  </label>
                  <span className={`text-[10px] ${overrideReason.trim().length >= 10 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {overrideReason.trim().length}/10 min chars
                  </span>
                </div>
                <textarea
                  rows={3}
                  required
                  placeholder="Enter detailed technical rationale (e.g. Eddy current NDT test confirmed defect is superficial tooling mark < 0.05mm; mechanical structural integrity intact)..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full p-2.5 bg-slate-950 rounded border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-400"
                />
                {overrideReason.trim().length > 0 && overrideReason.trim().length < 10 && (
                  <p className="text-[10px] text-rose-400 mt-1">
                    Audit reason must be at least 10 characters long to satisfy QMS regulatory requirements.
                  </p>
                )}
              </div>

              <label className="flex items-start gap-2 pt-1 text-[11px] text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={overrideCertified}
                  onChange={(e) => setOverrideCertified(e.target.checked)}
                  className="mt-0.5 rounded bg-slate-950 border-slate-700 text-amber-400 focus:ring-0"
                />
                <span>
                  I certify that this manual override adheres to ISO-9001 and MIL-STD standards, and will be committed to the permanent Redpanda audit log.
                </span>
              </label>
            </div>

            <div className="flex gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowOverrideModal(false)}
                className="flex-1 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={overrideReason.trim().length < 10 || !overrideCertified}
                onClick={handleSubmitOverride}
                className={`flex-1 py-2 rounded text-xs font-bold transition ${
                  overrideReason.trim().length >= 10 && overrideCertified
                    ? 'bg-amber-400 hover:bg-amber-300 text-slate-950'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
              >
                Confirm & Record Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
