import React, { useState, useEffect } from 'react';

export default function App() {
  const [inspection, setInspection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [sopInfo, setSopInfo] = useState('');
  const [apiStatus, setApiStatus] = useState('Checking...');
  const [erpSynced, setErpSynced] = useState(false);

  const API_BASE = import.meta.env.VITE_QC_API_BASE_URL || 'http://localhost:8002/api/qc';

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(d => setApiStatus(d.status))
      .catch(() => setApiStatus('Offline / Local Demo'));
  }, [API_BASE]);

  const runMockInspection = async (isDefective = true) => {
    setLoading(true);
    setErpSynced(false);
    setSopInfo('');

    // Emulate sending image and receiving ONNX detection
    setTimeout(() => {
      const mockBoxes = isDefective ? [
        {
          class_id: 0,
          class_name: 'surface_crack',
          confidence: 0.89,
          severity: 'CRITICAL',
          x_min: 0.28,
          y_min: 0.35,
          x_max: 0.48,
          y_max: 0.58,
          area_ratio: 0.046
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
          area_ratio: 0.015
        }
      ] : [
        {
          class_id: 3,
          class_name: 'color_defect',
          confidence: 0.62,
          severity: 'NEGLIGIBLE',
          x_min: 0.12,
          y_min: 0.12,
          x_max: 0.18,
          y_max: 0.18,
          area_ratio: 0.003
        }
      ];

      const verdict = isDefective ? 'QUARANTINE' : 'PASSED';
      const reasons = isDefective
        ? ['CRITICAL DEFECT DETECTED: Phát hiện vết nứt bề mặt (surface_crack). Yêu cầu cách ly lập tức.']
        : ['Tiêu chuẩn chất lượng đạt: Không có lỗi trọng yếu, bề mặt đạt dung sai xuất xưởng.'];

      const inspId = `INSP-2026-${Math.floor(1000 + Math.random() * 9000)}`;

      setInspection({
        id: inspId,
        item_code: 'ALU-CNC-001',
        batch_number: 'BATCH-2026-X1',
        latency_ms: 68.4,
        defects: mockBoxes,
        verdict: verdict,
        reasons: reasons,
        model_version: 'yolov8n-defect-v1.2-quantized'
      });

      // Populate Redpanda 8-event stream
      setEvents([
        { type: 'inspection.created', ts: '20:15:01.120', key: inspId, status: 'OK' },
        { type: 'inspection.image.uploaded', ts: '20:15:01.210', key: inspId, status: 'OK (R2 Store)' },
        { type: 'inspection.inference.completed', ts: '20:15:01.280', key: inspId, status: 'OK (68.4 ms)' },
        { type: 'inspection.quality.decided', ts: '20:15:01.285', key: inspId, status: `VERDICT: ${verdict}` },
      ]);

      setLoading(false);
    }, 450);
  };

  const handleSyncERP = async () => {
    if (!inspection) return;
    setLoading(true);

    setTimeout(() => {
      setEvents(prev => [
        ...prev,
        { type: 'inspection.review.completed', ts: '20:16:10.050', key: inspection.id, status: 'Inspector Approved' },
        { type: 'inspection.erp.sync.requested', ts: '20:16:10.120', key: inspection.id, status: 'Queued' },
        { type: 'inspection.erp.sync.completed', ts: '20:16:10.350', key: inspection.id, status: 'Doc: QI-2026-0089' },
      ]);
      setErpSynced(true);
      setLoading(false);
    }, 400);
  };

  const handleConsultSOP = (defectName) => {
    const sops = {
      surface_crack: 'SOP-QC-CRACK-01: Vết nứt bề mặt có nguy cơ nứt gãy cơ học. Cách ly chi tiết vào khay đỏ (Red Bin), gắn thẻ Quarantine, chuyển ảnh qua phòng Lab NDT.',
      dent_scratch: 'SOP-QC-SCRATCH-03: Vết lõm bề mặt nông (<0.2mm) có thể chuyển qua trạm mài bóng (Rework) để tái xử lý.',
      color_defect: 'SOP-QC-COLOR-04: Sai lệch màu Anodize chấp nhận được nếu Delta E < 2.0.'
    };
    setSopInfo(sops[defectName] || 'SOP tiêu chuẩn ISO 9001.');
  };

  return (
    <div className="flex flex-col h-screen max-w-7xl mx-auto p-4 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-amber-400">🔍 Visual QC & Defect Inspection (Product B)</h1>
          <p className="text-xs text-slate-400">YOLOv8 Quantized · ONNX CPU Inference (P50: 68.4ms) · Redpanda 8-Event Bus · ERPNext QI Sync</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span>API: <strong className="text-emerald-400">{apiStatus}</strong></span>
          </div>
          <div className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400">
            Engine: <strong className="text-sky-300">ONNX Runtime (2 Threads)</strong>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-4 mt-4 overflow-hidden">
        {/* Left Column: Image Canvas & Annotations (7 cols) */}
        <div className="col-span-7 flex flex-col bg-slate-900 rounded-xl border border-slate-800 p-4 overflow-hidden">
          <div className="flex justify-between items-center pb-3 border-b border-slate-800">
            <h2 className="text-sm font-bold text-slate-200">🖼️ Khung Quan Sát Bề Mặt Linh Kiện (640x640 Input)</h2>
            <div className="flex gap-2">
              <button
                onClick={() => runMockInspection(true)}
                className="px-3 py-1.5 bg-rose-600/80 hover:bg-rose-500 text-xs font-semibold rounded text-white"
              >
                ⚡ Test: Chi tiết có lỗi (Crack)
              </button>
              <button
                onClick={() => runMockInspection(false)}
                className="px-3 py-1.5 bg-emerald-600/80 hover:bg-emerald-500 text-xs font-semibold rounded text-white"
              >
                ✓ Test: Chi tiết đạt chuẩn (Pass)
              </button>
            </div>
          </div>

          {/* Canvas Simulation */}
          <div className="flex-1 relative mt-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center overflow-hidden">
            {/* Background Simulated CNC Part */}
            <div className="w-80 h-80 rounded-2xl bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900 border-4 border-slate-600 flex items-center justify-center relative shadow-2xl">
              <div className="w-40 h-40 rounded-full border-4 border-dashed border-slate-500/50 flex items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-slate-950/80"></div>
              </div>

              {/* Bounding Box Overlays */}
              {inspection && inspection.defects.map((d, i) => (
                <div
                  key={i}
                  style={{
                    position: 'absolute',
                    left: `${d.x_min * 100}%`,
                    top: `${d.y_min * 100}%`,
                    width: `${(d.x_max - d.x_min) * 100}%`,
                    height: `${(d.y_max - d.y_min) * 100}%`,
                  }}
                  onClick={() => handleConsultSOP(d.class_name)}
                  className={`border-2 cursor-pointer transition-all hover:scale-105 ${
                    d.severity === 'CRITICAL'
                      ? 'border-rose-500 bg-rose-500/20'
                      : d.severity === 'MAJOR'
                      ? 'border-amber-500 bg-amber-500/20'
                      : 'border-sky-400 bg-sky-400/20'
                  }`}
                >
                  <span className="absolute -top-5 left-0 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-900 text-white border border-slate-700 whitespace-nowrap">
                    {d.class_name} ({(d.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>

            {loading && (
              <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center text-xs text-amber-400 animate-pulse">
                <span>ONNX Runtime CPU Inference Forward Pass...</span>
              </div>
            )}
          </div>

          {/* Telemetry bar */}
          <div className="mt-3 pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
            <span>Thời gian suy luận: <strong className="text-emerald-400 font-mono">{inspection ? `${inspection.latency_ms} ms` : '--'}</strong></span>
            <span>Mô hình: <strong className="text-sky-300 font-mono">YOLOv8n-Quantized</strong></span>
            <span>Khung hình: <strong className="text-slate-300">1920x1080 -> 640x640</strong></span>
          </div>
        </div>

        {/* Right Column: Verdict, ERP Sync, Redpanda Events (5 cols) */}
        <div className="col-span-5 flex flex-col gap-3 overflow-hidden">
          {/* Quality Decision Card (Deterministic Rules) */}
          <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Quyết Định Chất Lượng (Deterministic Safety Gate)</h2>
            {inspection ? (
              <div className="mt-2 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-300">Mã phiếu: <strong>{inspection.id}</strong></span>
                  <span className={`px-2.5 py-1 rounded text-xs font-bold ${
                    inspection.verdict === 'PASSED'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : inspection.verdict === 'QUARANTINE'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                  }`}>
                    {inspection.verdict}
                  </span>
                </div>
                <div className="text-xs text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-800 space-y-1">
                  {inspection.reasons.map((r, i) => (
                    <p key={i}>• {r}</p>
                  ))}
                </div>
                <div className="pt-2 flex gap-2">
                  <button
                    disabled={erpSynced}
                    onClick={handleSyncERP}
                    className={`flex-1 py-2 rounded text-xs font-semibold ${
                      erpSynced
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                        : 'bg-amber-500 hover:bg-amber-400 text-slate-950'
                    }`}
                  >
                    {erpSynced ? '✓ Đã đồng bộ ERPNext QI' : '📤 Đồng bộ Quality Inspection'}
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 mt-2">Bấm 'Test' ở khung bên trái để bắt đầu kiểm tra ngoại quan.</p>
            )}
          </div>

          {/* Advisory SOP Guidance */}
          {sopInfo && (
            <div className="bg-slate-900 p-3.5 rounded-xl border border-sky-500/40 text-xs space-y-1">
              <div className="text-sky-400 font-bold uppercase">💡 Hướng Dẫn Thao Tác Chuẩn (Advisory SOP):</div>
              <p className="text-slate-200">{sopInfo}</p>
            </div>
          )}

          {/* Redpanda Kafka 8-Event Audit Stream */}
          <div className="flex-1 bg-slate-900 p-4 rounded-xl border border-slate-800 flex flex-col overflow-hidden">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wide flex justify-between items-center">
              <span>📡 Redpanda QC 8-Event Stream</span>
              <span className="text-[10px] text-emerald-400 font-mono">Topic: enterprise.qc.inspections</span>
            </h2>
            <div className="flex-1 mt-2.5 overflow-y-auto space-y-2 font-mono text-[11px]">
              {events.length > 0 ? (
                events.map((ev, idx) => (
                  <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                    <div>
                      <span className="text-amber-400 font-bold">{ev.type}</span>
                      <span className="text-slate-500 block text-[10px]">{ev.key} · {ev.ts}</span>
                    </div>
                    <span className="text-emerald-400 text-[10px]">{ev.status}</span>
                  </div>
                ))
              ) : (
                <p className="text-slate-600 text-xs">Chưa có sự kiện nào được phát sinh.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
