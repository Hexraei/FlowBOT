import React, { useState, useEffect, useRef } from 'react';
import { Send, X, Shield, User, Bot, AlertCircle } from 'lucide-react';
import { API_BASE, adminHeaders } from '../api';

interface Message {
  id: string;
  user_message: string;
  bot_response: string | null;
  sender_type: string;
  agent_name: string | null;
  created_at: string;
}

interface TakeoverPanelProps {
  sessionId: string;
  onClose: () => void;
}

export const TakeoverPanel: React.FC<TakeoverPanelProps> = ({ sessionId, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Replace polling with SSE stream
  useEffect(() => {
    const connectSSE = () => {
      if (sseRef.current) sseRef.current.close();
      const es = new EventSource(`${API_BASE}/api/stream/session/${sessionId}`);

      es.onmessage = (event) => {
        try {
          const ticket = JSON.parse(event.data);
          setMessages(prev => {
            const exists = prev.find(m => m.id === ticket.id);
            if (exists) return prev;
            return [...prev, ticket];
          });
        } catch (e) {
          console.error('SSE parse error:', e);
        }
      };

      es.onerror = () => {
        console.warn('TakeoverPanel SSE disconnected. Retrying in 3s...');
        es.close();
        setTimeout(connectSSE, 3000);
      };

      sseRef.current = es;
    };

    connectSSE();
    return () => sseRef.current?.close();
  }, [sessionId]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    setInput('');

    try {
      const agentName = localStorage.getItem('flowbot_agent_name') || 'Support Agent';
      const response = await fetch(`${API_BASE}/api/tickets/session/${sessionId}/message`, {
        method: 'POST',
        headers: adminHeaders,
        body: JSON.stringify({ message: text, agent_name: agentName })
      });

      if (!response.ok) {
        alert('Failed to send message.');
        setInput(text);
      }
    } catch (err) {
      console.error(err);
      alert('Error sending message.');
      setInput(text);
    } finally {
      setSending(false);
    }
  };

  // Helper to get initials
  const getInitials = (name: string) => {
    return name ? name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2) : 'OP';
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '560px',
        height: '100vh',
        backgroundColor: '#0c111e',
        borderLeft: '1px solid var(--border-glass)',
        boxShadow: '-8px 0 32px rgba(0,0,0,0.5)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(79, 70, 229, 0.03)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            color: 'var(--success)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Shield size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: '700', color: 'white' }}>
              Active Takeover Live Chat
            </h2>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
              Session: {sessionId.substring(5, 15)}...
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <X size={22} />
        </button>
      </div>

      {/* Message Stream */}
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', backgroundColor: 'rgba(7, 10, 19, 0.2)' }}>
        
        {messages.map((msg, index) => {
          // System Message
          if (msg.sender_type === 'system') {
            return (
              <div key={msg.id || index} style={{ 
                alignSelf: 'center', 
                backgroundColor: 'rgba(245, 158, 11, 0.1)', 
                border: '1px solid rgba(245, 158, 11, 0.15)',
                color: 'var(--warning)',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                margin: '12px 0'
              }}>
                <AlertCircle size={14} />
                {msg.user_message}
              </div>
            );
          }

          // Human Agent (Admin) Message
          if (msg.sender_type === 'agent') {
            return (
              <div key={msg.id || index} style={{ alignSelf: 'flex-end', maxWidth: '80%', display: 'flex', gap: '10px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-end' }}>
                  <span style={{ fontSize: '10.5px', color: 'var(--text-secondary)', fontWeight: '600' }}>
                    {msg.agent_name || 'Agent'} (You)
                  </span>
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '16px',
                    borderTopRightRadius: '4px',
                    backgroundColor: 'var(--primary)',
                    color: 'white',
                    fontSize: '13px',
                    lineHeight: '1.45'
                  }}>
                    {msg.user_message}
                  </div>
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(79, 70, 229, 0.2)',
                  color: 'var(--primary-hover)',
                  fontSize: '11px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  alignSelf: 'flex-start'
                }}>
                  {getInitials(msg.agent_name || 'Agent')}
                </div>
              </div>
            );
          }

          // User (Customer) Message
          // A customer message might have bot_response (if it was before takeover)
          return (
            <React.Fragment key={msg.id || index}>
              {/* User text */}
              <div style={{ alignSelf: 'flex-start', maxWidth: '80%', display: 'flex', gap: '10px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(14, 165, 233, 0.1)',
                  color: 'var(--secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  alignSelf: 'flex-start'
                }}>
                  <User size={15} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '10.5px', color: 'var(--text-secondary)', fontWeight: '600' }}>Customer</span>
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '16px',
                    borderTopLeftRadius: '4px',
                    backgroundColor: 'rgba(30, 41, 59, 0.65)',
                    border: '1px solid var(--border-glass)',
                    color: '#cbd5e1',
                    fontSize: '13px',
                    lineHeight: '1.45'
                  }}>
                    {msg.user_message}
                  </div>
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>

              {/* Bot response (if bot responded to this message in history before takeover) */}
              {msg.bot_response && msg.sender_type !== 'agent' && (
                <div style={{ alignSelf: 'flex-start', marginLeft: '42px', maxWidth: '80%', display: 'flex', gap: '10px' }}>
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    alignSelf: 'flex-start'
                  }}>
                    <Bot size={13} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '10.5px', color: 'var(--text-muted)', fontWeight: '500' }}>FlowBOT AI</span>
                    <div style={{
                      padding: '10px 14px',
                      borderRadius: '14px',
                      borderTopLeftRadius: '4px',
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid rgba(255, 255, 255, 0.03)',
                      color: '#94a3b8',
                      fontSize: '12.5px',
                      lineHeight: '1.4',
                      fontStyle: 'italic'
                    }}>
                      {msg.bot_response}
                    </div>
                  </div>
                </div>
              )}
            </React.Fragment>
          );
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* Input panel */}
      <form onSubmit={handleSend} style={{ padding: '20px 24px', borderTop: '1px solid var(--border-glass)', display: 'flex', gap: '12px', backgroundColor: 'var(--bg-main)' }}>
        <input
          type="text"
          placeholder="Type live message to customer..."
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={sending}
          style={{
            flex: 1,
            padding: '14px 18px',
            borderRadius: '10px',
            backgroundColor: '#0c111e',
            border: '1px solid var(--border-glass)',
            color: 'white',
            fontSize: '13px'
          }}
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          style={{
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            backgroundColor: 'var(--primary)',
            border: 'none',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={e => {
            if (!sending && input.trim()) e.currentTarget.style.backgroundColor = 'var(--primary-hover)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.backgroundColor = 'var(--primary)';
          }}
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};
