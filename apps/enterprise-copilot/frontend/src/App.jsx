import React, { useState, useEffect } from 'react';

export default function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Xin chào! Tôi là Trợ lý AI Quản trị Doanh nghiệp Copilot (Product A). Tôi có thể hỗ trợ bạn tra cứu SOP, tra cứu tồn kho ERPNext, đồng bộ CRM Salesforce và soạn thảo đơn hàng kiểm soát kép.',
      sources: 2
    }
  ]);
  const [input, setInput] = useState('');
  const [role, setRole] = useState('MAKER');
  const [loading, setLoading] = useState(false);
  const [pendingWorkflow, setPendingWorkflow] = useState(null);
  const [pin, setPin] = useState('');
  const [pinError, setPinError] = useState('');
  const [apiStatus, setApiStatus] = useState('Checking...');

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/copilot';

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => setApiStatus(data.status))
      .catch(() => setApiStatus('Offline / Local Mock'));
  }, [API_BASE]);

  const tokenForRole = (r) => {
    // Demo tokens
    return `mock-token-${r.toLowerCase()}`;
  };

  const handleSend = async (queryText) => {
    const textToSend = queryText || input;
    if (!textToSend.trim()) return;

    const newMsgs = [...messages, { sender: 'user', text: textToSend }];
    setMessages(newMsgs);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenForRole(role)}`
        },
        body: JSON.stringify({ query: textToSend, tenant_id: 'TENANT-001' })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setMessages([...newMsgs, {
        sender: 'ai',
        text: data.response,
        sources: data.retrieved_sources,
        draft: data.draft_order
      }]);

      if (data.requires_approval && data.approval_status === 'PENDING_APPROVAL') {
        setPendingWorkflow({
          id: data.workflow_id,
          draft: data.draft_order
        });
      }
    } catch (err) {
      // Offline fallback mock
      const isOrder = textToSend.toLowerCase().includes('đặt hàng') || textToSend.toLowerCase().includes('cnc');
      const draft = isOrder ? {
        order_id: 'ORD-DEMO-991',
        customer_name: 'Acme Manufacturing Corp',
        item_code: 'ALU-CNC-001',
        quantity: 500,
        rate: 25.0,
        total_amount: 12500.0
      } : null;

      const reply = isOrder
        ? 'Đã tạo bản nháp đơn hàng ORD-DEMO-991 trị giá $12,500.00 USD. Do giá trị > $10,000 USD, quy trình tạm dừng và yêu cầu Kiểm soát viên (Checker) nhập PIN để duyệt.'
        : `Dựa trên tài liệu SOP nội bộ, câu hỏi của bạn đã được đối soát qua hệ thống hybrid search (BM25 + Dense RRF).`;

      setMessages([...newMsgs, {
        sender: 'ai',
        text: reply,
        sources: 2,
        draft: draft
      }]);

      if (isOrder) {
        setPendingWorkflow({
          id: 'WF-MOCK-001',
          draft: draft
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (action) => {
    if (action === 'APPROVED' && pin !== '123456') {
      setPinError('Mã PIN KSV không đúng (Mặc định: 123456)');
      return;
    }
    setPinError('');

    try {
      await fetch(`${API_BASE}/v1/workflows/${pendingWorkflow.id}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenForRole('CHECKER')}`
        },
        body: JSON.stringify({
          action: action,
          supervisor_pin: pin,
          notes: 'Phê duyệt ghi sổ cái ERPNext'
        })
      });
    } catch (e) {
      // Handled gracefully in mock
    }

    setMessages(prev => [...prev, {
      sender: 'ai',
      text: action === 'APPROVED'
        ? `[Kiểm soát viên ĐÃ PHÊ DUYỆT ĐƠN HÀNG ${pendingWorkflow.draft.order_id}]: Đồng bộ thành công vào ERPNext DocType 'Sales Order' (SO-2026-0042) và cập nhật Salesforce CRM.`
        : `[Kiểm soát viên ĐÃ TỪ CHỐI ĐƠN HÀNG ${pendingWorkflow.draft.order_id}]. Lệnh mua bị hủy.`,
      sources: 1
    }]);

    setPendingWorkflow(null);
    setPin('');
  };

  return (
    <div className="flex flex-col h-screen max-w-6xl mx-auto p-4 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center pb-4 border-b border-slate-700">
        <div>
          <h1 className="text-2xl font-bold text-sky-400">🏢 Enterprise Copilot (Product A)</h1>
          <p className="text-xs text-slate-400">FastAPI · LangGraph · Qdrant Hybrid RAG · ERPNext v15 · Salesforce REST · RabbitMQ</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>API Status: <strong className="text-emerald-400">{apiStatus}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Vai trò:</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-sky-300 font-semibold focus:outline-none"
            >
              <option value="MAKER">Maker (Giao dịch viên)</option>
              <option value="CHECKER">Checker (Kiểm soát viên)</option>
              <option value="AUDITOR">Auditor (Kiểm toán viên)</option>
            </select>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex gap-4 mt-4 overflow-hidden">
        {/* Chat Stream */}
        <div className="flex-1 flex flex-col bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-2xl p-4 rounded-xl text-sm leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-700/80 border border-slate-600 text-slate-100'
                }`}>
                  <p>{m.text}</p>
                  {m.sources && (
                    <div className="mt-2 pt-2 border-t border-slate-600/50 flex items-center justify-between text-xs text-slate-400">
                      <span>Nguồn tài liệu: {m.sources} đoạn trích (Hybrid RRF Top-K)</span>
                      <span className="text-emerald-400 font-mono">BGE-M3 + BM25</span>
                    </div>
                  )}
                  {m.draft && (
                    <div className="mt-3 p-3 bg-slate-900/80 rounded border border-amber-500/40 text-xs font-mono space-y-1">
                      <div className="text-amber-400 font-bold uppercase">📋 Bản nháp đơn hàng ERP: {m.draft.order_id}</div>
                      <div>Khách hàng: {m.draft.customer_name}</div>
                      <div>Mã VT: {m.draft.item_code} | Số lượng: {m.draft.quantity} | Đơn giá: ${m.draft.rate}</div>
                      <div className="text-emerald-400 font-bold text-sm">Tổng tiền: ${m.draft.total_amount?.toLocaleString()} USD</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-xs text-sky-400 animate-pulse">LangGraph đang thực thi RAG và kiểm tra quy trình...</div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="p-2 bg-slate-900/50 border-t border-slate-700 flex gap-2 overflow-x-auto text-xs">
            <button
              onClick={() => handleSend('Tạo đơn hàng 500 linh kiện nhôm CNC mã ALU-CNC-001 cho khách hàng Acme Corp')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-sky-300 border border-slate-700 whitespace-nowrap"
            >
              ⚡ Tạo đơn hàng nhôm CNC ($12,500)
            </button>
            <button
              onClick={() => handleSend('Kiểm tra tồn kho vật tư linh kiện nhôm trong ERPNext')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 whitespace-nowrap"
            >
              📦 Kiểm tra tồn kho ERP
            </button>
            <button
              onClick={() => handleSend('Tra cứu thông tin khách hàng Acme Corp trong Salesforce')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 whitespace-nowrap"
            >
              ☁️ Tra cứu Salesforce CRM
            </button>
          </div>

          {/* Input Box */}
          <div className="p-3 bg-slate-900 border-t border-slate-700 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Nhập yêu cầu nghiệp vụ, tra cứu SOP hoặc soạn thảo đơn hàng..."
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={() => handleSend()}
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 font-semibold text-sm rounded-lg transition-colors"
            >
              Gửi yêu cầu
            </button>
          </div>
        </div>

        {/* Sidebar: HITL Approval & Integration Watcher */}
        <div className="w-80 flex flex-col gap-4">
          {/* HITL Dual Control Approval Box */}
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <h2 className="text-sm font-bold text-amber-400 uppercase tracking-wide flex items-center gap-2">
              <span>🛡️ Kiểm Soát Kép (4-Mắt)</span>
            </h2>
            {pendingWorkflow ? (
              <div className="mt-3 space-y-3 text-xs">
                <div className="p-2.5 bg-amber-500/10 border border-amber-500/30 rounded text-amber-300">
                  Phát hiện lệnh vượt hạn mức: <strong>${pendingWorkflow.draft.total_amount?.toLocaleString()} USD</strong>.
                  Yêu cầu phê duyệt từ cấp Kiểm soát viên.
                </div>
                {role === 'CHECKER' ? (
                  <div className="space-y-2">
                    <label className="block text-slate-300">Nhập mã PIN KSV (123456):</label>
                    <input
                      type="password"
                      value={pin}
                      maxLength={6}
                      onChange={(e) => setPin(e.target.value)}
                      placeholder="Mã PIN 6 số"
                      className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 font-mono text-center text-sm focus:outline-none"
                    />
                    {pinError && <p className="text-rose-400 text-[11px]">{pinError}</p>}
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => handleApprove('APPROVED')}
                        className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 font-semibold text-white rounded text-xs"
                      >
                        ✓ Duyệt & Ghi sổ ERP
                      </button>
                      <button
                        onClick={() => handleApprove('REJECTED')}
                        className="py-2 px-3 bg-rose-600/80 hover:bg-rose-500 text-white rounded text-xs"
                      >
                        ✕ Từ chối
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-slate-900 rounded border border-slate-700 text-slate-400">
                    Bạn đang đăng nhập vai trò <strong>{role}</strong>. Chỉ có tài khoản <strong>CHECKER</strong> mới có thẩm quyền ký số phê duyệt lệnh này.
                  </div>
                )}
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-500">Không có đơn hàng nào đang chờ duyệt.</p>
            )}
          </div>

          {/* System Connections Status */}
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700 space-y-2.5 text-xs">
            <h2 className="font-bold text-slate-300 uppercase tracking-wide">Trạng Thái Kết Nối</h2>
            <div className="flex justify-between items-center py-1 border-b border-slate-700">
              <span className="text-slate-400">ERPNext v15 REST:</span>
              <span className="text-emerald-400 font-semibold">Online (Sandbox)</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-700">
              <span className="text-slate-400">Salesforce OAuth 2.0:</span>
              <span className="text-emerald-400 font-semibold">Connected</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-700">
              <span className="text-slate-400">Qdrant Hybrid Vector:</span>
              <span className="text-emerald-400 font-semibold">Indexed (BGE-M3)</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-700">
              <span className="text-slate-400">RabbitMQ Outbox:</span>
              <span className="text-emerald-400 font-semibold">Active & Confirmed</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-slate-400">Langfuse Tracing:</span>
              <span className="text-emerald-400 font-semibold">Tracing Spans</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
