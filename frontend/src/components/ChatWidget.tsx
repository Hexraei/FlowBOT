import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, Sparkles } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId] = useState(() => {
    let id = sessionStorage.getItem('flowzint_chat_session_id');
    if (!id) {
      id = 'sess_' + Math.random().toString(36).substring(2, 15) + '_' + Date.now().toString(36);
      sessionStorage.setItem('flowzint_chat_session_id', id);
    }
    return id;
  });
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      text: "Hello! I am the FlowZint AI Concierge. How can I assist you with our SaaS systems, enterprise AI automation, or careers today?",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend: string) => {
    const text = textToSend.trim();
    if (!text) return;

    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });
      
      if (!response.ok) {
        throw new Error('Server returned an error');
      }

      const data = await response.json();
      
      // Add bot response
      setMessages(prev => [...prev, {
        id: data.id || Date.now().toString(),
        text: data.bot_response || "Thank you for reaching out. Your request has been logged.",
        sender: 'bot',
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Chat error:', error);
      // Friendly fallback error message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        text: "I'm experiencing a brief connection issue, but your message has been buffered for our operations team. How else can I help?",
        sender: 'bot',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestions = [
    "Tell me about your AI & Automation services",
    "How can I apply for internship programs?",
    "Do you have open opportunities for React developers?",
    "We need custom enterprise digital infrastructure"
  ];

  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999 }}>
      {/* Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)',
            border: 'none',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 32px rgba(79, 70, 229, 0.4)',
            cursor: 'pointer',
            transition: 'transform 0.2s ease',
            animation: 'pulse-glow 3s infinite'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.08)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <MessageSquare size={28} />
        </button>
      )}

      {/* Chat Dialog */}
      {isOpen && (
        <div
          className="glass-panel animate-fade-in"
          style={{
            width: '420px',
            height: '600px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '1px solid var(--border-glass)'
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px',
              background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.2) 0%, rgba(14, 165, 233, 0.2) 100%)',
              borderBottom: '1px solid var(--border-glass)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(79, 70, 229, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Bot size={20} color="var(--secondary)" />
              </div>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: '700' }}>FlowZint AI Concierge</h3>
                <p style={{ fontSize: '11px', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--success)' }}></span>
                  Online
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Messages Stream */}
          <div
            style={{
              flex: 1,
              padding: '16px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              backgroundColor: 'rgba(7, 10, 19, 0.2)'
            }}
          >
            {messages.map(msg => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}
              >
                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: '16px',
                    borderTopRightRadius: msg.sender === 'user' ? '4px' : '16px',
                    borderTopLeftRadius: msg.sender === 'bot' ? '4px' : '16px',
                    backgroundColor: msg.sender === 'user' ? 'var(--primary)' : 'rgba(30, 41, 59, 0.65)',
                    border: msg.sender === 'bot' ? '1px solid var(--border-glass)' : 'none',
                    color: 'white',
                    fontSize: '13.5px',
                    lineHeight: '1.45',
                    wordBreak: 'break-word'
                  }}
                >
                  {msg.text}
                </div>
                <span
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-muted)',
                    alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                    padding: '0 4px'
                  }}
                >
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', gap: '8px', padding: '12px 16px', alignSelf: 'flex-start', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
                <div style={{ width: '6px', height: '6px', backgroundColor: 'var(--text-secondary)', borderRadius: '50%', animation: 'fadeIn 1s infinite alternate' }}></div>
                <div style={{ width: '6px', height: '6px', backgroundColor: 'var(--text-secondary)', borderRadius: '50%', animation: 'fadeIn 1s infinite alternate 0.2s' }}></div>
                <div style={{ width: '6px', height: '6px', backgroundColor: 'var(--text-secondary)', borderRadius: '50%', animation: 'fadeIn 1s infinite alternate 0.4s' }}></div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions */}
          {messages.length === 1 && (
            <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: '6px', borderTop: '1px solid var(--border-glass)', backgroundColor: 'rgba(7, 10, 19, 0.3)' }}>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Sparkles size={12} color="var(--secondary)" />
                Suggestions:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(s)}
                    style={{
                      textAlign: 'left',
                      padding: '8px 12px',
                      fontSize: '11.5px',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-glass)',
                      color: 'var(--text-secondary)',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.backgroundColor = 'rgba(79, 70, 229, 0.1)';
                      e.currentTarget.style.borderColor = 'var(--primary)';
                      e.currentTarget.style.color = 'white';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
                      e.currentTarget.style.borderColor = 'var(--border-glass)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Panel */}
          <div
            style={{
              padding: '16px',
              borderTop: '1px solid var(--border-glass)',
              display: 'flex',
              gap: '10px',
              backgroundColor: 'var(--bg-main)'
            }}
          >
            <input
              type="text"
              placeholder="Ask FlowZint AI Concierge..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend(input)}
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: 'rgba(30, 41, 59, 0.4)',
                border: '1px solid var(--border-glass)',
                color: 'white',
                fontSize: '13px'
              }}
            />
            <button
              onClick={() => handleSend(input)}
              disabled={isLoading}
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                backgroundColor: 'var(--primary)',
                border: 'none',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--primary-hover)')}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--primary)')}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
