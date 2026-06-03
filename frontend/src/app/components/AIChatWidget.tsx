import { FormEvent, useEffect, useRef, useState } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  X,
  RefreshCw,
  AlertCircle,
  User,
  Loader2,
  ChevronDown,
  Trash2,
} from 'lucide-react';
import { aiAssistantAPI, AIMessage, getApiError, AIQuickReportType } from '../services/api';

// ---------- Tezkor tugmalar ----------
type QuickAction = { id: AIQuickReportType; label: string };

const QUICK_ACTIONS: QuickAction[] = [
  { id: 'team_analysis',       label: 'Jamoani tahlil qilish' },
  { id: 'player_assessment',   label: "O'yinchilarni baholash" },
  { id: 'training_plan',       label: "Mashg'ulot rejasi" },
  { id: 'strengths_weaknesses',label: 'Kuchli va zaif tomonlar' },
  { id: 'next_match',          label: "Keyingi o'yin tavsiyalari" },
];

// ---------- Vaqtni formatlash ----------
function fmtTime(iso: string) {
  try {
    const d = new Date(iso);
    return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
  } catch { return ''; }
}

// ---------- localStorage chat tarixi ----------
const STORAGE_KEY = 'ai_chat_history';
const CONV_ID_KEY  = 'ai_conv_id';

function loadMessages(): AIMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}
function saveMessages(msgs: AIMessage[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-100))); }
  catch { /* storage to'la bo'lishi mumkin */ }
}
function loadConvId(): number | null {
  const v = localStorage.getItem(CONV_ID_KEY);
  return v ? Number(v) : null;
}
function saveConvId(id: number | null) {
  if (id) localStorage.setItem(CONV_ID_KEY, String(id));
  else     localStorage.removeItem(CONV_ID_KEY);
}

// ============================================================
export default function AIChatWidget() {
  const [open,           setOpen]           = useState(false);
  const [messages,       setMessages]       = useState<AIMessage[]>(loadMessages);
  const [conversationId, setConversationId] = useState<number | null>(loadConvId);
  const [inputValue,     setInputValue]     = useState('');
  const [loading,        setLoading]        = useState(false);
  const [isTyping,       setIsTyping]       = useState(false);
  const [error,          setError]          = useState('');
  const [showQuick,      setShowQuick]      = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef    = useRef<HTMLTextAreaElement>(null);

  // Xabarlar o'zgarganda localStorage ga saqlash
  useEffect(() => { saveMessages(messages); }, [messages]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, open]);

  // Textarea auto-resize
  useEffect(() => {
    const el = textareaRef.current;
    if (el) { el.style.height = 'auto'; el.style.height = `${el.scrollHeight}px`; }
  }, [inputValue]);

  // Chat ochilganda inputga focus
  useEffect(() => {
    if (open) setTimeout(() => textareaRef.current?.focus(), 100);
  }, [open]);

  // ---------- Xabar yuborish ----------
  const sendMessage = async (message: string) => {
    if (!message.trim() || loading) return;
    setError('');
    setLoading(true);
    setIsTyping(true);
    setShowQuick(false);

    const userMsg: AIMessage = {
      id: Date.now(),
      role: 'user',
      role_display: 'Siz',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');

    try {
      const res = await aiAssistantAPI.chat(message, conversationId);
      if (!conversationId && res.conversation_id) {
        setConversationId(res.conversation_id);
        saveConvId(res.conversation_id);
      }
      setMessages(prev => [...prev, res.ai_message]);
    } catch (err) {
      setError(getApiError(err, 'AI javob berishda xatolik yuz berdi.'));
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  // ---------- Tezkor tugma ----------
  const handleQuick = async (actionId: AIQuickReportType) => {
    const action = QUICK_ACTIONS.find(a => a.id === actionId);
    const label = action?.label || actionId;

    setError('');
    setLoading(true);
    setIsTyping(true);
    setShowQuick(false);

    const userMsg: AIMessage = {
      id: Date.now(),
      role: 'user',
      role_display: 'Siz',
      content: label,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await aiAssistantAPI.quickReport(actionId);
      const aiMsg: AIMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        role_display: 'AI Murabbiy',
        content: res.content || res.report || '',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      setError(getApiError(err, 'Hisobot yaratishda xatolik yuz berdi.'));
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  // ---------- Suhbatni tozalash ----------
  const clearChat = () => {
    setMessages([]);
    setConversationId(null);
    saveConvId(null);
    setError('');
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  return (
    <>
      {/* ---- Chat oynasi ---- */}
      {open && (
        <div className="ai-widget-panel">
          {/* Panel sarlavhasi */}
          <div className="ai-widget-header">
            <div className="ai-widget-header-left">
              <div className="ai-widget-avatar-icon">
                <Bot size={18} />
              </div>
              <div>
                <span className="ai-widget-title">AI Murabbiy</span>
              </div>
            </div>
            <div className="ai-widget-header-actions">
              {messages.length > 0 && (
                <button
                  type="button"
                  className="ai-widget-icon-btn"
                  onClick={clearChat}
                  title="Suhbatni tozalash"
                >
                  <Trash2 size={15} />
                </button>
              )}
              <button
                type="button"
                className="ai-widget-icon-btn"
                onClick={() => setOpen(false)}
                title="Yopish"
              >
                <ChevronDown size={18} />
              </button>
            </div>
          </div>

          {/* Xabarlar maydoni */}
          <div className="ai-widget-messages">
            {messages.length === 0 && (
              <div className="ai-widget-empty">
                <Bot size={36} />
                <p>Salom! Men AI Murabbiy Yordamchisiman.</p>
                <p>Jamoangiz haqida savol bering yoki tezkor tugmalardan foydalaning.</p>
              </div>
            )}

            {messages.map(msg => (
              <div
                key={msg.id}
                className={`ai-widget-msg ${msg.role === 'user' ? 'ai-widget-msg-user' : 'ai-widget-msg-ai'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="ai-widget-msg-avatar"><Bot size={14} /></div>
                )}
                <div className="ai-widget-msg-body">
                  <div className="ai-widget-msg-text">{msg.content}</div>
                  <span className="ai-widget-msg-time">{fmtTime(msg.created_at)}</span>
                </div>
                {msg.role === 'user' && (
                  <div className="ai-widget-msg-avatar ai-widget-msg-avatar-user"><User size={14} /></div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="ai-widget-msg ai-widget-msg-ai">
                <div className="ai-widget-msg-avatar"><Bot size={14} /></div>
                <div className="ai-widget-msg-body">
                  <div className="ai-widget-typing">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Xatolik */}
          {error && (
            <div className="ai-widget-error">
              <AlertCircle size={14} />
              <span>{error}</span>
              <button type="button" onClick={() => setError('')}>
                <X size={12} />
              </button>
            </div>
          )}

          {/* Tezkor tugmalar */}
          {showQuick && (
            <div className="ai-widget-quick-panel">
              {QUICK_ACTIONS.map(a => (
                <button
                  key={a.id}
                  type="button"
                  className="ai-widget-quick-btn"
                  onClick={() => handleQuick(a.id)}
                  disabled={loading}
                >
                  <Sparkles size={13} />
                  {a.label}
                </button>
              ))}
            </div>
          )}

          {/* Input maydoni */}
          <form className="ai-widget-input-row" onSubmit={handleSubmit}>
            <button
              type="button"
              className={`ai-widget-quick-toggle ${showQuick ? 'active' : ''}`}
              onClick={() => setShowQuick(v => !v)}
              title="Tezkor tugmalar"
              disabled={loading}
            >
              <Sparkles size={16} />
            </button>
            <textarea
              ref={textareaRef}
              className="ai-widget-textarea"
              placeholder="Savol yozing..."
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={1}
            />
            <button
              type="submit"
              className="ai-widget-send-btn"
              disabled={loading || !inputValue.trim()}
              title="Yuborish"
            >
              {loading
                ? <Loader2 size={16} className="ai-widget-spin" />
                : <Send size={16} />
              }
            </button>
          </form>
        </div>
      )}

      {/* ---- Suzuvchi tugma ---- */}
      <button
        type="button"
        className={`ai-widget-fab ${open ? 'ai-widget-fab-open' : ''}`}
        onClick={() => setOpen(v => !v)}
        aria-label="AI Murabbiy chatbotini ochish"
        title="AI Murabbiy"
      >
        {open ? <X size={24} /> : <Bot size={24} />}
        {!open && messages.length > 0 && (
          <span className="ai-widget-fab-badge">{messages.filter(m => m.role === 'assistant').length}</span>
        )}
      </button>
    </>
  );
}
