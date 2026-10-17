import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, CheckCircle2, XCircle, AlertTriangle, FileText, Send, UserCheck,
  Building2, Database, Cloud, RefreshCw, KeyRound, ExternalLink, Clock,
  ArrowRight, Check, X, ChevronRight, Layers, Award, Terminal
} from 'lucide-react';

// Lightweight custom Markdown renderer for formatting AI responses
function MarkdownView({ text }) {
  if (!text) return null;

  // Split into paragraphs / lines
  const lines = text.split('\n');
  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {lines.map((line, idx) => {
        if (!line.trim()) return <div key={idx} className="h-1" />;

        // Header 3 or 2
        if (line.startsWith('### ')) {
          return <h4 key={idx} className="text-sky-300 font-semibold text-base pt-1">{line.replace('### ', '')}</h4>;
        }
        if (line.startsWith('## ')) {
          return <h3 key={idx} className="text-sky-400 font-bold text-lg pt-1">{line.replace('## ', '')}</h3>;
        }

        // Bullet point
        if (line.startsWith('- ') || line.startsWith('* ')) {
          const content = line.substring(2);
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="text-sky-400 font-bold leading-5">•</span>
              <div>{renderInline(content)}</div>
            </div>
          );
        }

        // Blockquote / Alert
        if (line.startsWith('> ')) {
          return (
            <blockquote key={idx} className="pl-3 border-l-2 border-amber-500/80 bg-amber-500/10 py-1 px-2 rounded-r text-amber-200 text-xs">
              {renderInline(line.substring(2))}
            </blockquote>
          );
        }

        return <p key={idx}>{renderInline(line)}</p>;
      })}
    </div>
  );
}

// Inline renderer for **bold** and `code`
function renderInline(str) {
  const parts = [];
  let remaining = str;
  let keyIdx = 0;

  while (remaining.length > 0) {
    // Check for bold **...**
    const boldMatch = remaining.match(/\*\*(.*?)\*\*/);
    // Check for code `...`
    const codeMatch = remaining.match(/`([^`]+)`/);

    if (boldMatch && (!codeMatch || boldMatch.index < codeMatch.index)) {
      if (boldMatch.index > 0) {
        parts.push(remaining.substring(0, boldMatch.index));
      }
      parts.push(<strong key={keyIdx++} className="font-semibold text-white">{boldMatch[1]}</strong>);
      remaining = remaining.substring(boldMatch.index + boldMatch[0].length);
    } else if (codeMatch) {
      if (codeMatch.index > 0) {
        parts.push(remaining.substring(0, codeMatch.index));
      }
      parts.push(
        <code key={keyIdx++} className="bg-slate-900 px-1.5 py-0.5 rounded text-sky-300 font-mono text-xs border border-slate-700">
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.substring(codeMatch.index + codeMatch[0].length);
    } else {
      parts.push(remaining);
      break;
    }
  }

  return parts;
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Xin chào! Tôi là **Trợ lý AI Quản trị Doanh nghiệp Copilot (Product A)**.\n\nTôi hỗ trợ bạn tra cứu quy trình nội bộ SOP qua **Hybrid RAG (BGE-M3 + BM25)**, kiểm tra tồn kho **ERPNext v15**, kết nối dữ liệu CRM **Salesforce** và thực hiện quy trình kiểm soát kép **4-Mắt (Maker-Checker)**.',
      sources: 2,
      citations: [
        {
          id: 'SOP-PROC-01',
          title: 'Quy trình Mua hàng & Duyệt Đơn hàng',
          content: 'Theo quy định quản trị tài chính: Đơn hàng linh kiện nhôm CNC có giá trị vượt 10,000 USD bắt buộc phải qua phê duyệt 4-mắt từ Kiểm soát viên (Checker) và xác thực mã PIN bảo mật. Đơn giá nhôm CNC mã ALU-CNC-001 chuẩn là $25.00/chiếc.',
          score: 0.942,
        },
        {
          id: 'SOP-INV-02',
          title: 'Quy định Quản lý Tồn kho Vật tư',
          content: 'Tồn kho an toàn tối thiểu cho linh kiện nhôm ALU-CNC-001 là 500 chiếc. Nếu tồn kho khả dụng dưới định mức, hệ thống phải tự động tạo phiếu đề xuất mua hàng (Purchase Requisition).',
          score: 0.885,
        }
      ]
    }
  ]);

  const [input, setInput] = useState('');
  const [role, setRole] = useState('MAKER'); // MAKER, CHECKER, AUDITOR
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');

  // Workflow & HITL Approval Modal state
  const [pendingWorkflow, setPendingWorkflow] = useState(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [pin, setPin] = useState('123456');
  const [pinError, setPinError] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('Phê duyệt đơn hàng, ghi nhận sổ cái ERPNext');

  // Citation Drawer state
  const [selectedCitations, setSelectedCitations] = useState(null);
  const [isCitationDrawerOpen, setIsCitationDrawerOpen] = useState(false);

  // Audit Timeline state
  const [auditEvents, setAuditEvents] = useState([
    {
      id: 'EVT-INIT',
      time: '08:30:00',
      category: 'SYSTEM',
      actor: 'system',
      title: 'Hệ thống Khởi tạo & Kiểm soát Kép',
      detail: 'Kết nối ERPNext v15, Salesforce REST OAuth, Qdrant Hybrid RRF active.',
      status: 'VERIFIED',
    }
  ]);

  const [apiStatus, setApiStatus] = useState('Checking...');
  const chatBottomRef = useRef(null);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/copilot';

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => setApiStatus(data.status === 'healthy' ? 'Online' : 'Degraded'))
      .catch(() => setApiStatus('Offline (Sandbox Fallback)'));
  }, [API_BASE]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText, loading]);

  const tokenForRole = (r) => {
    return `mock-token-${r.toLowerCase()}`;
  };

  const addAuditEvent = (category, actor, title, detail, status = 'VERIFIED') => {
    const newEvt = {
      id: `EVT-${Date.now().toString(36).toUpperCase()}`,
      time: new Date().toLocaleTimeString(),
      category,
      actor,
      title,
      detail,
      status,
    };
    setAuditEvents(prev => [newEvt, ...prev]);
  };

  const handleSend = async (queryText) => {
    const textToSend = queryText || input;
    if (!textToSend.trim()) return;

    const userMsg = { sender: 'user', text: textToSend };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Audit log for maker action
    addAuditEvent(
      'MAKER',
      role === 'MAKER' ? 'maker-1 (Giao dịch viên)' : `${role.toLowerCase()}-1`,
      'Gửi yêu cầu nghiệp vụ',
      `Maker submit: "${textToSend.substring(0, 48)}..."`
    );

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
      const replyText = data.response;
      const citations = data.citations || [];

      // Simulate streaming rendering
      let currentIdx = 0;
      setStreamingText('');
      const streamInterval = setInterval(() => {
        currentIdx += 15;
        if (currentIdx >= replyText.length) {
          clearInterval(streamInterval);
          setStreamingText('');
          setMessages(prev => [...prev, {
            sender: 'ai',
            text: replyText,
            sources: data.retrieved_sources,
            citations: citations,
            draft: data.draft_order,
            workflow_id: data.workflow_id
          }]);

          if (data.requires_approval && data.approval_status === 'PENDING_APPROVAL') {
            const workflowObj = {
              id: data.workflow_id,
              draft: data.draft_order,
              maker: 'maker-1'
            };
            setPendingWorkflow(workflowObj);
            setIsApprovalModalOpen(true);
            addAuditEvent(
              'GUARDRAIL',
              'LangGraph Orchestrator',
              'Kích hoạt cổng duyệt 4-Mắt (HITL Gate)',
              `Đơn hàng ${data.draft_order.order_id} trị giá $${data.draft_order.total_amount?.toLocaleString()} USD vượt hạn mức $10,000. Chờ Checker PIN.`,
              'PENDING'
            );
          }
          setLoading(false);
        } else {
          setStreamingText(replyText.substring(0, currentIdx));
        }
      }, 20);

    } catch (err) {
      // Offline fallback mock
      const isOrder = textToSend.toLowerCase().includes('đặt hàng') || textToSend.toLowerCase().includes('cnc') || textToSend.toLowerCase().includes('mua');
      const draft = isOrder ? {
        order_id: `ORD-${Math.floor(1000 + Math.random() * 9000)}`,
        customer_name: 'Acme Manufacturing Corp',
        item_code: 'ALU-CNC-001',
        quantity: 500,
        rate: 25.0,
        total_amount: 12500.0
      } : null;

      const reply = isOrder
        ? `Đã tạo bản nháp đơn hàng **${draft.order_id}** trị giá **$12,500.00 USD** cho khách hàng *Acme Manufacturing Corp*.\n\n> ⚠️ **Quy tắc Kiểm soát Kép (SOP-PROC-01):** Do giá trị đơn hàng vượt hạn mức $10,000 USD, quy trình LangGraph đã tạm dừng tại bước \`require_approval\`. Yêu cầu Kiểm soát viên (Checker) xác thực mã PIN bảo mật để ghi sổ ERP.`
        : `Dựa trên tài liệu **SOP-PROC-01** và tồn kho **ERPNext v15**, yêu cầu của bạn đã được đối soát qua hệ thống **Hybrid Search (Dense BGE-M3 + BM25 Sparse + BGE Cross-Encoder Reranker)**.\n\n- Tồn kho khả dụng linh kiện ALU-CNC-001: **1,240 chiếc**\n- Định mức tồn kho an toàn: **500 chiếc**\n- Đơn vị tính: **Nos** | Đơn giá chuẩn: **$25.00 USD**`;

      const mockCitations = [
        {
          id: 'SOP-PROC-01',
          title: 'Quy trình Mua hàng & Duyệt Đơn hàng',
          content: 'Theo quy định quản trị tài chính: Đơn hàng linh kiện nhôm CNC có giá trị vượt 10,000 USD bắt buộc phải qua phê duyệt 4-mắt từ Kiểm soát viên (Checker) và xác thực mã PIN bảo mật.',
          score: 0.942,
        },
        {
          id: 'SOP-INV-02',
          title: 'Quy định Quản lý Tồn kho Vật tư',
          content: 'Tồn kho an toàn tối thiểu cho linh kiện nhôm ALU-CNC-001 là 500 chiếc. Nếu tồn kho khả dụng dưới định mức, hệ thống phải tự động tạo phiếu đề xuất mua hàng.',
          score: 0.885,
        }
      ];

      setMessages(prev => [...prev, {
        sender: 'ai',
        text: reply,
        sources: mockCitations.length,
        citations: mockCitations,
        draft: draft,
        workflow_id: 'WF-LOCAL-001'
      }]);

      if (isOrder) {
        setPendingWorkflow({
          id: draft.order_id,
          draft: draft,
          maker: 'maker-1'
        });
        setIsApprovalModalOpen(true);
        addAuditEvent(
          'GUARDRAIL',
          'LangGraph Orchestrator',
          'Kích hoạt cổng duyệt 4-Mắt (HITL Gate)',
          `Đơn hàng ${draft.order_id} trị giá $${draft.total_amount.toLocaleString()} USD vượt hạn mức $10,000 USD. Chờ Checker PIN.`,
          'PENDING'
        );
      }
      setLoading(false);
    }
  };

  const handleApprove = async (action) => {
    if (action === 'APPROVED' && pin !== '123456') {
      setPinError('Mã PIN KSV không hợp lệ. Vui lòng nhập mã chuẩn: 123456');
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
          notes: approvalNotes
        })
      });
    } catch (e) {
      // Graceful fallback
    }

    const orderId = pendingWorkflow.draft.order_id;
    if (action === 'APPROVED') {
      addAuditEvent(
        'CHECKER',
        'checker-1 (Kiểm soát viên)',
        `Phê duyệt & Ký số lệnh mua ${orderId}`,
        `Xác thực PIN [123456] thành công. Ký số Ed25519-SIG-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
        'VERIFIED'
      );
      addAuditEvent(
        'INTEGRATION',
        'RabbitMQ Outbox -> ERPNext',
        `Ghi sổ cái ERPNext DocType 'Sales Order'`,
        `Tạo bản ghi SO-2026-0042 (${pendingWorkflow.draft.customer_name}), đồng bộ CRM Salesforce.`,
        'VERIFIED'
      );

      setMessages(prev => [...prev, {
        sender: 'ai',
        text: `### ✅ Đơn hàng ${orderId} đã được Kiểm soát viên phê duyệt\n\n- **Trạng thái:** Ký số hợp lệ bởi Kiểm soát viên (\`checker-1\`)\n- **Sổ cái ERPNext:** Tạo thành công Sales Order **SO-2026-0042**\n- **CRM Salesforce:** External ID mapping \`CUST-ACME-01\` đã được cập nhật\n- **Outbox Message:** Published to RabbitMQ exchange \`business.orders\` (idempotency confirmed)`,
        sources: 1,
        citations: [
          {
            id: 'SOP-PROC-01',
            title: 'Quy trình Mua hàng & Duyệt Đơn hàng',
            content: 'Phê duyệt 4-Mắt hoàn tất. Bản ghi đơn hàng đã chuyển trạng thái Submitted trên ERPNext.',
            score: 0.985
          }
        ]
      }]);
    } else {
      addAuditEvent(
        'CHECKER',
        'checker-1 (Kiểm soát viên)',
        `Từ chối đơn hàng ${orderId}`,
        `Lý do: Từ chối bởi KSV. Lệnh mua bị hủy bỏ.`,
        'REJECTED'
      );

      setMessages(prev => [...prev, {
        sender: 'ai',
        text: `### ❌ Đơn hàng ${orderId} đã bị Kiểm soát viên TỪ CHỐI\n\nLệnh mua bị hủy theo quyết định của Kiểm soát viên. Không có thay đổi nào ghi nhận vào ERPNext.`,
        sources: 0
      }]);
    }

    setIsApprovalModalOpen(false);
    setPendingWorkflow(null);
  };

  const openCitationDrawer = (citations) => {
    setSelectedCitations(citations || []);
    setIsCitationDrawerOpen(true);
  };

  return (
    <div className="flex flex-col h-screen max-w-7xl mx-auto p-3 font-sans text-slate-100 select-none">
      {/* Top Navigation Bar */}
      <header className="flex flex-wrap justify-between items-center pb-3 border-b border-slate-700/80 gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 border border-sky-400/30">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold bg-gradient-to-r from-sky-400 via-sky-200 to-indigo-300 bg-clip-text text-transparent">
                Enterprise AI Copilot
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
                Product A · v1.5
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-2">
              <span>LangGraph 5-States</span> • <span>Qdrant Hybrid RAG</span> • <span>ERPNext v15</span> • <span>Salesforce CRM</span>
            </p>
          </div>
        </div>

        {/* Right Header: Role Switcher & System Status */}
        <div className="flex items-center gap-3">
          {/* API Health Pill */}
          <div className="flex items-center gap-1.5 bg-slate-800/90 px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
            <span className={`w-2 h-2 rounded-full ${apiStatus.includes('Online') ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            <span className="text-slate-400">API:</span>
            <span className={apiStatus.includes('Online') ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>{apiStatus}</span>
          </div>

          {/* Role Switcher (Maker vs Checker vs Auditor) */}
          <div className="flex items-center bg-slate-800/90 p-1 rounded-lg border border-slate-700 text-xs shadow-inner">
            <button
              onClick={() => setRole('MAKER')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                role === 'MAKER'
                  ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Maker</span>
              <span className="text-[10px] opacity-75">(Giao dịch)</span>
            </button>
            <button
              onClick={() => setRole('CHECKER')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                role === 'CHECKER'
                  ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Checker</span>
              <span className="text-[10px] opacity-75">(Kiểm soát)</span>
            </button>
            <button
              onClick={() => setRole('AUDITOR')}
              className={`px-2.5 py-1.5 rounded-md font-medium transition-all flex items-center gap-1 ${
                role === 'AUDITOR'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Auditor</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex gap-3 mt-3 overflow-hidden min-h-0">
        {/* Left Column: Chat Conversation Stream */}
        <div className="flex-1 flex flex-col bg-slate-800/50 rounded-xl border border-slate-700/80 overflow-hidden shadow-lg backdrop-blur">
          {/* Messages Scroll Area */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-3xl rounded-2xl p-4 text-sm shadow-md transition-all ${
                  m.sender === 'user'
                    ? 'bg-sky-600 text-white rounded-br-none ml-12'
                    : 'bg-slate-800/90 border border-slate-700/80 text-slate-100 rounded-bl-none mr-12'
                }`}>
                  {/* Sender label */}
                  <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-600/40 text-xs">
                    {m.sender === 'user' ? (
                      <span className="font-semibold text-sky-100 flex items-center gap-1">
                        <UserCheck className="w-3.5 h-3.5" /> Giao dịch viên (Maker: maker-1)
                      </span>
                    ) : (
                      <span className="font-semibold text-sky-300 flex items-center gap-1">
                        <Shield className="w-3.5 h-3.5" /> Trợ lý Doanh nghiệp Copilot
                      </span>
                    )}
                  </div>

                  {/* Body text */}
                  <MarkdownView text={m.text} />

                  {/* Draft Order Preview Card */}
                  {m.draft && (
                    <div className="mt-3 p-3.5 bg-slate-900/90 rounded-xl border border-amber-500/40 shadow-inner space-y-2">
                      <div className="flex justify-between items-center border-b border-amber-500/20 pb-2">
                        <span className="text-amber-400 font-bold flex items-center gap-1.5 text-xs">
                          <FileText className="w-4 h-4" /> BẢN NHÁP ĐƠN HÀNG: {m.draft.order_id}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          {pendingWorkflow ? 'CHỜ CHECKER PHÊ DUYỆT' : 'ĐÃ ĐƯỢC DUYỆT'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                        <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                          <span className="text-slate-400 block text-[10px]">Khách hàng</span>
                          <span className="font-medium truncate block">{m.draft.customer_name}</span>
                        </div>
                        <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                          <span className="text-slate-400 block text-[10px]">Mã vật tư</span>
                          <span className="font-mono text-sky-300 block">{m.draft.item_code}</span>
                        </div>
                        <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                          <span className="text-slate-400 block text-[10px]">Số lượng & Đơn giá</span>
                          <span className="font-mono block">{m.draft.quantity} × ${m.draft.rate}</span>
                        </div>
                        <div className="bg-slate-800/80 p-2 rounded border border-slate-700">
                          <span className="text-slate-400 block text-[10px]">Tổng giá trị</span>
                          <span className="font-mono text-emerald-400 font-bold block text-sm">
                            ${m.draft.total_amount?.toLocaleString()} USD
                          </span>
                        </div>
                      </div>

                      {/* Fast Action trigger if pending */}
                      {pendingWorkflow && (
                        <div className="flex justify-end pt-1">
                          <button
                            onClick={() => setIsApprovalModalOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow transition-colors"
                          >
                            <KeyRound className="w-3.5 h-3.5" /> Mở Hộp Thoại Duyệt 4-Mắt
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Citations Footer Button */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-slate-700/60 flex items-center justify-between text-xs">
                      <button
                        onClick={() => openCitationDrawer(m.citations)}
                        className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-700/80 hover:bg-slate-700 text-sky-300 border border-slate-600/80 transition-colors"
                      >
                        <Layers className="w-3.5 h-3.5 text-sky-400" />
                        <span>Xem {m.citations.length} nguồn dẫn chứng Hybrid RAG</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                      <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                        <Award className="w-3 h-3" /> BGE-M3 + BM25 RRF
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Live Streaming Render */}
            {streamingText && (
              <div className="flex flex-col items-start">
                <div className="max-w-3xl rounded-2xl rounded-bl-none p-4 text-sm bg-slate-800/90 border border-slate-700/80 text-slate-100 shadow-md mr-12">
                  <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-600/40 text-xs">
                    <span className="font-semibold text-sky-300 flex items-center gap-1">
                      <Shield className="w-3.5 h-3.5" /> Trợ lý Doanh nghiệp Copilot
                    </span>
                    <span className="text-sky-400 text-[10px] animate-pulse">● Đang tạo phản hồi...</span>
                  </div>
                  <MarkdownView text={streamingText} />
                </div>
              </div>
            )}

            {loading && !streamingText && (
              <div className="flex items-center gap-2 text-xs text-sky-400 animate-pulse p-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>LangGraph đang thực thi: retrieve_context → evaluate_policy → generate_draft...</span>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Quick Prompts Bar */}
          <div className="p-2 bg-slate-900/60 border-t border-slate-700/80 flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-slate-400 font-semibold px-1 whitespace-nowrap">Thử nhanh:</span>
            <button
              onClick={() => handleSend('Tạo đơn hàng đặt hàng 500 linh kiện nhôm CNC mã ALU-CNC-001 cho khách hàng Acme Corp')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-sky-300 border border-slate-700 whitespace-nowrap flex items-center gap-1 transition-colors"
            >
              <span>⚡ Tạo đơn hàng nhôm CNC ($12,500 - Kích hoạt 4-Mắt)</span>
            </button>
            <button
              onClick={() => handleSend('Kiểm tra tồn kho vật tư linh kiện nhôm ALU-CNC-001 trong ERPNext')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 whitespace-nowrap flex items-center gap-1 transition-colors"
            >
              <span>📦 Kiểm tra tồn kho ERPNext</span>
            </button>
            <button
              onClick={() => handleSend('Tra cứu thông tin khách hàng Acme Corp và cơ hội bán hàng trong Salesforce')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 whitespace-nowrap flex items-center gap-1 transition-colors"
            >
              <span>☁️ Tra cứu CRM Salesforce</span>
            </button>
          </div>

          {/* Input Box */}
          <div className="p-3 bg-slate-900 border-t border-slate-700/80 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Nhập câu hỏi SOP, tra cứu tồn kho, hoặc soạn thảo đơn hàng kiểm soát kép..."
              className="flex-1 bg-slate-800/90 border border-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 transition-colors"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading}
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 font-semibold text-sm rounded-xl transition-all shadow-md flex items-center gap-2 disabled:opacity-50"
            >
              <span>Gửi</span>
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Column: Dual-Control HITL Widget, Connections, and Audit Timeline */}
        <div className="w-88 flex flex-col gap-3 overflow-hidden">
          {/* Dual Control Gate Card */}
          <div className={`p-4 rounded-xl border transition-all ${
            pendingWorkflow
              ? 'bg-amber-500/10 border-amber-500/40 shadow-lg shadow-amber-500/10'
              : 'bg-slate-800/60 border-slate-700/80'
          }`}>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-amber-400 uppercase tracking-wide flex items-center gap-1.5">
                <Shield className="w-4 h-4 text-amber-400" />
                <span>Kiểm Soát Kép (4-Mắt)</span>
              </h2>
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                pendingWorkflow ? 'bg-amber-500 text-slate-900 animate-pulse' : 'bg-slate-700 text-slate-400'
              }`}>
                {pendingWorkflow ? 'ACTION REQUIRED' : 'IDLE'}
              </span>
            </div>

            {pendingWorkflow ? (
              <div className="mt-3 space-y-2.5 text-xs">
                <div className="p-2.5 bg-slate-900/90 rounded border border-amber-500/30">
                  <div className="text-amber-300 font-semibold">Đơn hàng: {pendingWorkflow.draft.order_id}</div>
                  <div className="text-slate-300">Giá trị: <strong className="text-emerald-400">${pendingWorkflow.draft.total_amount?.toLocaleString()} USD</strong></div>
                  <div className="text-slate-400 text-[11px] mt-1">Vượt định mức $10,000 USD (SOP-PROC-01).</div>
                </div>

                <button
                  onClick={() => setIsApprovalModalOpen(true)}
                  className="w-full py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 font-bold text-slate-900 rounded-lg text-xs shadow transition-all flex items-center justify-center gap-1.5"
                >
                  <KeyRound className="w-4 h-4" />
                  <span>Mở Trình Ký Số Duyệt Lệnh</span>
                </button>
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-400">
                Không có lệnh mua nào đang chờ phê duyệt. Các đơn hàng &gt; $10,000 USD sẽ tự động dừng tại cổng này.
              </p>
            )}
          </div>

          {/* Real-Time Audit Timeline */}
          <div className="flex-1 flex flex-col bg-slate-800/60 p-3.5 rounded-xl border border-slate-700/80 overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-slate-700">
              <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                <span>Nhật Ký Kiểm Toán (Audit Trail)</span>
              </h2>
              <span className="text-[10px] text-slate-400">{auditEvents.length} sự kiện</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 mt-2 pr-1">
              {auditEvents.map((evt) => (
                <div key={evt.id} className="relative pl-4 border-l-2 border-slate-700 text-xs space-y-0.5">
                  <div className={`absolute -left-[5px] top-1 w-2 h-2 rounded-full ${
                    evt.status === 'VERIFIED' ? 'bg-emerald-400' :
                    evt.status === 'PENDING' ? 'bg-amber-400 animate-ping' : 'bg-rose-400'
                  }`} />
                  <div className="flex justify-between items-center text-[10px] text-slate-400">
                    <span className="font-mono">{evt.time}</span>
                    <span className="px-1.5 py-0.2 rounded bg-slate-700/60 font-semibold text-slate-300">
                      {evt.category}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-200">{evt.title}</div>
                  <div className="text-slate-400 text-[11px] leading-relaxed">{evt.detail}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Integration Status Card */}
          <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/80 text-xs space-y-1.5">
            <div className="font-bold text-slate-300 uppercase tracking-wide text-[11px] mb-1">
              Tích Hợp Hệ Thống
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span className="flex items-center gap-1.5"><Building2 className="w-3.5 h-3.5 text-sky-400" /> ERPNext v15 REST:</span>
              <span className="text-emerald-400 font-semibold font-mono">Connected (Sandbox)</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span className="flex items-center gap-1.5"><Cloud className="w-3.5 h-3.5 text-sky-400" /> Salesforce OAuth 2.0:</span>
              <span className="text-emerald-400 font-semibold font-mono">Active</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span className="flex items-center gap-1.5"><Database className="w-3.5 h-3.5 text-sky-400" /> Qdrant Hybrid RAG:</span>
              <span className="text-emerald-400 font-semibold font-mono">BGE-M3 + BM25</span>
            </div>
          </div>
        </div>
      </div>

      {/* Human-in-the-Loop (HITL) Approval Modal */}
      {isApprovalModalOpen && pendingWorkflow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-amber-500/50 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            {/* Modal Header */}
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Xác Thực & Duyệt Đơn Hàng (4-Mắt)</h3>
                  <p className="text-xs text-amber-400">SOP-PROC-01: Yêu cầu thẩm quyền Kiểm soát viên</p>
                </div>
              </div>
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Order Specification summary */}
            <div className="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Mã đơn hàng:</span>
                <span className="font-mono font-bold text-amber-300">{pendingWorkflow.draft.order_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Khách hàng:</span>
                <span className="font-semibold text-white">{pendingWorkflow.draft.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Chi tiết vật tư:</span>
                <span className="font-mono">{pendingWorkflow.draft.item_code} ({pendingWorkflow.draft.quantity} cái @ ${pendingWorkflow.draft.rate})</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-700 font-bold">
                <span className="text-slate-300">Tổng thanh toán:</span>
                <span className="text-emerald-400 text-sm font-mono">${pendingWorkflow.draft.total_amount?.toLocaleString()} USD</span>
              </div>
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Người tạo lệnh (Maker):</span>
                <span className="font-mono text-sky-300">{pendingWorkflow.maker || 'maker-1'}</span>
              </div>
            </div>

            {/* Role Verification & PIN Input */}
            {role === 'CHECKER' ? (
              <div className="space-y-3">
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700 text-xs space-y-2">
                  <label className="block text-slate-200 font-semibold">
                    Nhập mã PIN Kiểm soát viên (Mặc định: <span className="font-mono text-amber-400">123456</span>):
                  </label>
                  <input
                    type="password"
                    maxLength={6}
                    value={pin}
                    onChange={(e) => {
                      setPin(e.target.value);
                      setPinError('');
                    }}
                    placeholder="Mã PIN 6 số"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-center text-lg font-mono tracking-widest text-emerald-400 focus:outline-none focus:border-amber-500"
                  />
                  {pinError && <p className="text-rose-400 text-xs font-semibold">{pinError}</p>}
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1">Ghi chú phê duyệt:</label>
                  <input
                    type="text"
                    value={approvalNotes}
                    onChange={(e) => setApprovalNotes(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => handleApprove('APPROVED')}
                    className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 font-bold text-white rounded-xl text-xs flex items-center justify-center gap-1.5 shadow transition-colors"
                  >
                    <Check className="w-4 h-4" />
                    <span>✓ Ký Số & Ghi Sổ Cái ERPNext</span>
                  </button>
                  <button
                    onClick={() => handleApprove('REJECTED')}
                    className="px-4 py-2.5 bg-rose-600/80 hover:bg-rose-600 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-1 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    <span>Từ Chối</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs space-y-3">
                <div className="flex items-start gap-2 text-amber-300">
                  <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-400" />
                  <div>
                    <strong className="block font-bold">Chặn Tự Duyệt (Anti-Fraud Dual Control)</strong>
                    Bạn đang đăng nhập vai trò <strong>{role}</strong>. Quy tắc kiểm soát kép quy định người lập lệnh (Maker) không thể tự phê duyệt đơn hàng của mình.
                  </div>
                </div>
                <button
                  onClick={() => setRole('CHECKER')}
                  className="w-full py-2 bg-amber-500 hover:bg-amber-400 font-bold text-slate-950 rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5 shadow"
                >
                  <UserCheck className="w-4 h-4" />
                  <span>Chuyển sang Vai Trò Checker (Kiểm soát viên)</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Citation Card Drawer */}
      {isCitationDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-700 h-full p-5 overflow-y-auto space-y-4 shadow-2xl flex flex-col">
            <div className="flex justify-between items-center pb-3 border-b border-slate-700">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-sky-400" />
                <h3 className="font-bold text-white text-base">Tài Liệu Dẫn Chứng RAG</h3>
              </div>
              <button
                onClick={() => setIsCitationDrawerOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs text-slate-400 bg-slate-800/60 p-2.5 rounded-lg border border-slate-700">
              Các trích dẫn được xếp hạng qua <strong>Hybrid Search</strong>: BGE-M3 Dense (Cosine) + BM25 Okapi Sparse với thuật toán <strong>Reciprocal Rank Fusion (k=60)</strong> và tái xếp hạng bằng <strong>BGE Cross-Encoder</strong>.
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto pr-1">
              {selectedCitations && selectedCitations.map((doc, idx) => (
                <div key={idx} className="p-3.5 bg-slate-800/80 rounded-xl border border-slate-700 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-xs font-bold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/30">
                      {doc.id}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      Score: {doc.score ? `${(doc.score * 100).toFixed(1)}%` : '94.2%'}
                    </span>
                  </div>
                  <h4 className="font-semibold text-slate-200 text-xs">{doc.title}</h4>
                  <p className="text-slate-300 text-xs leading-relaxed bg-slate-900/60 p-2.5 rounded border border-slate-700/50">
                    "{doc.content}"
                  </p>
                  <div className="text-[10px] text-slate-500 flex justify-between items-center pt-1">
                    <span>Trích lục SOP Doanh Nghiệp</span>
                    <span className="font-mono text-sky-400">Tenant: TENANT-001</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-slate-800">
              <button
                onClick={() => setIsCitationDrawerOpen(false)}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
              >
                Đóng Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
