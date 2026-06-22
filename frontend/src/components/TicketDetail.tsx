import React, { useState, useEffect } from 'react';
import { X, Check, ArrowRight, MessageSquare, User, BadgeAlert } from 'lucide-react';
import { API_BASE, adminHeaders } from '../api';

interface Ticket {
  id: string;
  session_id: string | null;
  created_at: string;
  user_message: string;
  bot_response: string;
  intent: string;
  severity: string;
  sentiment: string;
  probable_component: string;
  urgency: number;
  contact_details: string;
  confidence_score: number;
  cluster_id: string | null;
  status: string;
  github_issue_url: string | null;
  discord_notified: boolean;
}

interface TicketDetailProps {
  ticketId: string;
  onClose: () => void;
  onUpdate: () => void;
  onJoinChat: (sessionId: string) => void;
}

export const TicketDetail: React.FC<TicketDetailProps> = ({ ticketId, onClose, onUpdate, onJoinChat }) => {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [escalating, setEscalating] = useState(false);
  
  // Form edit states
  const [intent, setIntent] = useState('');
  const [severity, setSeverity] = useState('');
  const [sentiment, setSentiment] = useState('');
  const [component, setComponent] = useState('');
  const [urgency, setUrgency] = useState(3);
  const [contact, setContact] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    fetchTicket();
  }, [ticketId]);

  const fetchTicket = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/tickets/${ticketId}`, { headers: adminHeaders });
      if (response.ok) {
        const data = await response.json();
        setTicket(data);
        setIntent(data.intent || 'other');
        setSeverity(data.severity || 'low');
        setSentiment(data.sentiment || 'neutral');
        setComponent(data.probable_component || 'General');
        setUrgency(data.urgency || 3);
        setContact(data.contact_details || '');
        setStatus(data.status || 'pending_review');
      }
    } catch (error) {
      console.error('Error fetching ticket detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/tickets/${ticketId}`, {
        method: 'PUT',
        headers: adminHeaders,
        body: JSON.stringify({ intent, severity, sentiment, probable_component: component, urgency, contact_details: contact, status })
      });
      if (response.ok) {
        alert('Ticket specifications successfully updated.');
        onUpdate();
        fetchTicket();
      }
    } catch (error) {
      console.error('Error saving ticket:', error);
      alert('Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };

  const handleHandoff = async () => {
    setEscalating(true);
    try {
      const response = await fetch(`${API_BASE}/api/tickets/${ticketId}/handoff`, {
        method: 'POST',
        headers: adminHeaders
      });
      if (response.ok) {
        alert('Handoff integrations executed successfully!');
        onUpdate();
        fetchTicket();
      }
    } catch (error) {
      console.error('Handoff error:', error);
      alert('Failed to trigger handoffs.');
    } finally {
      setEscalating(false);
    }
  };

  const [joiningChat, setJoiningChat] = useState(false);

  const handleJoinChat = async () => {
    if (!ticket || !ticket.session_id) return;
    setJoiningChat(true);
    try {
      const agentName = localStorage.getItem('flowbot_agent_name') || 'Support Agent';
      const response = await fetch(`${API_BASE}/api/tickets/session/${ticket.session_id}/takeover`, {
        method: 'POST',
        headers: adminHeaders,
        body: JSON.stringify({ agent_name: agentName })
      });
      if (response.ok) {
        onJoinChat(ticket.session_id);
      } else {
        alert('Failed to takeover session.');
      }
    } catch (err) {
      console.error(err);
      alert('Error connecting to takeover API.');
    } finally {
      setJoiningChat(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        Loading ticket parameters...
      </div>
    );
  }

  if (!ticket) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--danger)' }}>
        Ticket not found.
      </div>
    );
  }


  return (
    <>
      {/* Backdrop overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(5, 8, 16, 0.6)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          zIndex: 999,
          animation: 'fadeInSimple 0.25s ease-out forwards'
        }}
      />

      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '560px',
          height: '100vh',
          backgroundColor: '#0c111e',
          borderRight: '1px solid var(--border-glass)',
          boxShadow: '8px 0 32px rgba(0,0,0,0.5)',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInLeft 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards'
        }}
      >
      {/* Drawer Header */}
      <div
        style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255,255,255,0.01)'
        }}
      >
        <div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
            ID: {ticket.id}
          </span>
          <h2 style={{ fontSize: '18px', fontWeight: '700', marginTop: '2px' }}>
            Review Support Intelligence Card
          </h2>
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

      {/* Drawer Body (Scrollable) */}
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* User Query Block */}
        <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)' }}>
          <h4 style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <User size={14} color="var(--secondary)" />
            Customer Conversation:
          </h4>
          <p style={{ fontSize: '14px', lineHeight: '1.5', color: '#cbd5e1', whiteSpace: 'pre-wrap' }}>
            {ticket.user_message}
          </p>
        </div>

        {/* AI response Block */}
        <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: 'rgba(79, 70, 229, 0.05)', border: '1px solid rgba(79, 70, 229, 0.15)' }}>
          <h4 style={{ fontSize: '13px', color: 'var(--primary-hover)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <BadgeAlert size={14} />
            Concierge Response:
          </h4>
          <p style={{ fontSize: '13.5px', lineHeight: '1.5', color: '#cbd5e1', fontStyle: 'italic' }}>
            {ticket.bot_response}
          </p>
        </div>

        {/* Edit Specifications Form */}
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '14px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '6px' }}>
            Structured Metadata (AI Classifications)
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Intent */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Intent Category</label>
              <select
                value={intent}
                onChange={e => setIntent(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option value="business_enquiry">Business Enquiry</option>
                <option value="partnership">Partnership</option>
                <option value="contact_info">Contact Info</option>
                <option value="careers">Careers</option>
                <option value="internship_programs">Internship Programs</option>
                <option value="open_opportunities">Open Opportunities</option>
                <option value="hiring_process">Hiring Process</option>
                <option value="service_inquiry">Service Inquiry</option>
                <option value="other">Other / General</option>
              </select>
            </div>

            {/* Severity */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Severity Level</label>
              <select
                value={severity}
                onChange={e => setSeverity(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Sentiment */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Sentiment</label>
              <select
                value={sentiment}
                onChange={e => setSentiment(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
                <option value="frustrated">Frustrated</option>
              </select>
            </div>

            {/* Urgency */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Urgency Priority (1-5)</label>
              <select
                value={urgency}
                onChange={e => setUrgency(Number(e.target.value))}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option value="1">1 (Lowest)</option>
                <option value="2">2</option>
                <option value="3">3 (Normal)</option>
                <option value="4">4</option>
                <option value="5">5 (Critical)</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Component */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Probable Component</label>
              <input
                type="text"
                value={component}
                onChange={e => setComponent(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
              />
            </div>

            {/* Ticket status */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Queue Status</label>
              <select
                value={status}
                onChange={e => setStatus(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
              >
                <option value="pending_review">Pending Review</option>
                <option value="handoff_completed">Handoff Completed</option>
                <option value="resolved">Resolved</option>
                <option value="ignored">Ignored</option>
              </select>
            </div>
          </div>

          {/* Contact Details */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Contact details (extracted)</label>
            <input
              type="text"
              value={contact}
              onChange={e => setContact(e.target.value)}
              placeholder="e.g. email or phone number"
              style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#131929', border: '1px solid var(--border-glass)', color: 'white' }}
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            style={{
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: 'rgba(255,255,255,0.08)',
              border: '1px solid var(--border-glass)',
              color: 'white',
              fontSize: '13px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginTop: '6px'
            }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.15)';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.08)';
              e.currentTarget.style.borderColor = 'var(--border-glass)';
            }}
          >
            <Check size={16} />
            {saving ? 'Saving Specs...' : 'Save Specs Correction'}
          </button>
        </form>

        {/* Integration Handoff escalation section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', borderTop: '1px solid var(--border-glass)', paddingTop: '20px' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
            Downstream Operations & Escalation
          </h3>
          
          <button
            onClick={handleHandoff}
            disabled={escalating}
            style={{
              padding: '14px',
              borderRadius: '10px',
              backgroundColor: 'var(--primary)',
              border: 'none',
              color: 'white',
              fontSize: '13.5px',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 16px rgba(79, 70, 229, 0.2)'
            }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--primary-hover)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--primary)')}
          >
            <ArrowRight size={18} />
            {escalating ? 'Processing Escalations...' : 'Trigger Operations Handoff'}
          </button>

          {ticket.session_id && (
            <button
              onClick={handleJoinChat}
              disabled={joiningChat}
              style={{
                padding: '14px',
                borderRadius: '10px',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid var(--success)',
                color: 'var(--success)',
                fontSize: '13.5px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 16px rgba(16, 185, 129, 0.1)'
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'rgba(16, 185, 129, 0.25)')}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'rgba(16, 185, 129, 0.15)')}
            >
              <Check size={18} />
              {joiningChat ? 'Joining Chat...' : 'Join Live Chat Takeover'}
            </button>
          )}

          {/* Integration Status Indicators */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MessageSquare size={15} />
                GitHub issue card
              </span>
              {ticket.github_issue_url ? (
                <a
                  href={ticket.github_issue_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: '11px', color: 'var(--secondary)', textDecoration: 'none', fontFamily: 'monospace' }}
                >
                  [View Issue Card]
                </a>
              ) : (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Not Created</span>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MessageSquare size={15} />
                Discord Slack notification
              </span>
              {ticket.discord_notified ? (
                <span style={{ fontSize: '11px', color: 'var(--success)', fontWeight: '600' }}>Dispatched</span>
              ) : (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Pending Dispatch</span>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
    </>
  );
};
