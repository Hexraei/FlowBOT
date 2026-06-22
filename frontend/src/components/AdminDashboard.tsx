import React, { useState, useEffect } from 'react';
import { RefreshCw, Search, ShieldAlert, Layers, Smile, MessageCircle, SlidersHorizontal, CheckSquare, Eye } from 'lucide-react';
import { TicketDetail } from './TicketDetail';

interface Ticket {
  id: string;
  created_at: string;
  user_message: string;
  bot_response: string;
  summary?: string;
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

interface Cluster {
  id: string;
  name: string;
  description: string;
  created_at: string;
  ticket_count: number;
}

export const AdminDashboard: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  
  // Filter and search states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('pending_review');
  const [severityFilter, setSeverityFilter] = useState('');
  const [intentFilter, setIntentFilter] = useState('');

  useEffect(() => {
    fetchDashboardData();
    
    // Automatically refresh dashboard statistics every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [statusFilter, severityFilter, intentFilter]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Build query string
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (severityFilter) params.append('severity', severityFilter);
      if (intentFilter) params.append('intent', intentFilter);

      const [ticketsResponse, clustersResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/tickets?${params.toString()}`),
        fetch('http://localhost:8000/api/clusters')
      ]);

      if (ticketsResponse.ok && clustersResponse.ok) {
        const ticketsData = await ticketsResponse.json();
        const clustersData = await clustersResponse.json();
        setTickets(ticketsData);
        setClusters(clustersData);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredTickets = () => {
    return tickets.filter(t => 
      t.user_message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.summary && t.summary.toLowerCase().includes(searchTerm.toLowerCase())) ||
      t.id.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  // KPIs calculations
  const totalCount = tickets.length;
  const highSeverityCount = tickets.filter(t => t.severity === 'high').length;
  const pendingReviewCount = tickets.filter(t => t.status === 'pending_review').length;
  const frustratedCount = tickets.filter(t => t.sentiment === 'frustrated' || t.sentiment === 'negative').length;

  const getSeverityBadge = (sev: string) => {
    let bg = 'rgba(16, 185, 129, 0.1)';
    let color = 'var(--success)';
    if (sev === 'high') {
      bg = 'rgba(239, 68, 68, 0.1)';
      color = 'var(--danger)';
    } else if (sev === 'medium') {
      bg = 'rgba(245, 158, 11, 0.1)';
      color = 'var(--warning)';
    }
    return (
      <span style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', backgroundColor: bg, color }}>
        {sev.toUpperCase()}
      </span>
    );
  };

  const getIntentBadge = (intent: string) => {
    let bg = 'rgba(255, 255, 255, 0.05)';
    let color = 'var(--text-secondary)';
    
    if (intent === 'business_enquiry') {
      bg = 'rgba(14, 165, 233, 0.1)';
      color = 'var(--secondary)';
    } else if (intent === 'partnership') {
      bg = 'rgba(217, 70, 239, 0.1)';
      color = 'var(--accent)';
    } else if (intent.includes('intern') || intent.includes('career') || intent.includes('hiring')) {
      bg = 'rgba(79, 70, 229, 0.1)';
      color = 'var(--primary-hover)';
    } else if (intent === 'service_inquiry') {
      bg = 'rgba(245, 158, 11, 0.1)';
      color = 'var(--warning)';
    }
    
    return (
      <span style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', backgroundColor: bg, color, border: '1px solid rgba(255,255,255,0.02)' }}>
        {intent.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    let bg = 'rgba(255, 255, 255, 0.05)';
    let color = 'var(--text-secondary)';
    if (status === 'handoff_completed') {
      bg = 'rgba(79, 70, 229, 0.15)';
      color = 'var(--primary-hover)';
    } else if (status === 'resolved') {
      bg = 'rgba(16, 185, 129, 0.15)';
      color = 'var(--success)';
    } else if (status === 'pending_review') {
      bg = 'rgba(245, 158, 11, 0.15)';
      color = 'var(--warning)';
    } else if (status === 'resolved_by_ai') {
      bg = 'rgba(14, 165, 233, 0.15)';
      color = '#38bdf8';
    }
    return (
      <span style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', backgroundColor: bg, color }}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  return (
    <div style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
      
      {/* Dashboard Top bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', letterSpacing: '-0.025em' }}>
            FlowZint Support Intelligence Hub
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14.5px', marginTop: '4px' }}>
            Triaging incoming visitor requests, qualifying intents, and routing handoffs.
          </p>
        </div>
        
        <button
          onClick={fetchDashboardData}
          style={{
            padding: '10px 16px',
            borderRadius: '10px',
            backgroundColor: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--border-glass)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13.5px',
            fontWeight: '600'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.08)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.04)';
          }}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh Data
        </button>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
        {/* KPI 1 */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(14, 165, 233, 0.1)', color: 'var(--secondary)' }}>
            <MessageCircle size={24} />
          </div>
          <div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>Total Support Tickets</p>
            <h2 style={{ fontSize: '24px', fontWeight: '800', marginTop: '4px' }}>{totalCount}</h2>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)' }}>
            <CheckSquare size={24} />
          </div>
          <div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>Pending Manual Reviews</p>
            <h2 style={{ fontSize: '24px', fontWeight: '800', marginTop: '4px' }}>{pendingReviewCount}</h2>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}>
            <ShieldAlert size={24} />
          </div>
          <div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>Critical / High Severity</p>
            <h2 style={{ fontSize: '24px', fontWeight: '800', marginTop: '4px' }}>{highSeverityCount}</h2>
          </div>
        </div>

        {/* KPI 4 */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(217, 70, 239, 0.1)', color: 'var(--accent)' }}>
            <Smile size={24} />
          </div>
          <div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>Frustrated Customers</p>
            <h2 style={{ fontSize: '24px', fontWeight: '800', marginTop: '4px' }}>{frustratedCount}</h2>
          </div>
        </div>
      </div>

      {/* Main Grid: Clusters Panel & Ticket List */}
      <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '32px' }}>
        
        {/* Left Column: Active Clusters */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="var(--secondary)" />
            Active Issue Clusters ({clusters.length})
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {clusters.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }} className="glass-panel">
                No active clusters found.
              </div>
            ) : (
              clusters.map(c => (
                <div key={c.id} className="glass-panel" style={{ padding: '16px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                    <h4 style={{ fontSize: '13.5px', fontWeight: '700', color: 'white' }}>{c.name}</h4>
                    <span style={{ padding: '3px 6px', borderRadius: '4px', fontSize: '10.5px', fontWeight: '700', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                      {c.ticket_count}
                    </span>
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: '1.4' }}>
                    {c.description}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Tickets Table Panel */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflow: 'hidden' }}>
          {/* Filters Top Bar */}
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
              <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="Search ticket body, summary, or ID..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 16px 10px 36px',
                  borderRadius: '8px',
                  backgroundColor: '#0c111e',
                  border: '1px solid var(--border-glass)',
                  color: 'white',
                  fontSize: '13px'
                }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <SlidersHorizontal size={16} color="var(--text-muted)" />
              
              {/* Intent Filter */}
              <select
                value={intentFilter}
                onChange={e => setIntentFilter(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#0c111e', border: '1px solid var(--border-glass)', color: 'var(--text-secondary)', fontSize: '12.5px' }}
              >
                <option value="">All Intents</option>
                <option value="business_enquiry">Business Enquiry</option>
                <option value="partnership">Partnership</option>
                <option value="careers">Careers</option>
                <option value="internship_programs">Internship Programs</option>
                <option value="service_inquiry">Service Inquiry</option>
                <option value="other">Other</option>
              </select>

              {/* Severity Filter */}
              <select
                value={severityFilter}
                onChange={e => setSeverityFilter(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#0c111e', border: '1px solid var(--border-glass)', color: 'var(--text-secondary)', fontSize: '12.5px' }}
              >
                <option value="">All Severities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#0c111e', border: '1px solid var(--border-glass)', color: 'var(--text-secondary)', fontSize: '12.5px' }}
              >
                <option value="">All Statuses</option>
                <option value="pending_review">Pending Review</option>
                <option value="resolved_by_ai">Resolved by AI</option>
                <option value="handoff_completed">Handoff Completed</option>
                <option value="resolved">Resolved</option>
                <option value="ignored">Ignored</option>
              </select>
            </div>
          </div>

          {/* Table Container */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-secondary)', fontSize: '12.5px' }}>
                  <th style={{ padding: '12px 16px', fontWeight: '600' }}>Timestamp</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600' }}>Conversation Message</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600' }}>Intent</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600' }}>Severity</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600' }}>Urgency</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600' }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {getFilteredTickets().length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                      No tickets match the filtered criteria.
                    </td>
                  </tr>
                ) : (
                  getFilteredTickets().map(t => (
                    <tr
                      key={t.id}
                      style={{
                        borderBottom: '1px solid rgba(255,255,255,0.03)',
                        fontSize: '13px',
                        transition: 'background 0.2s'
                      }}
                      onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.01)')}
                      onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '14px 16px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                        {new Date(t.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td style={{ padding: '14px 16px', color: '#cbd5e1', fontWeight: '500', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {t.user_message}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        {getIntentBadge(t.intent || 'other')}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        {getSeverityBadge(t.severity || 'low')}
                      </td>
                      <td style={{ padding: '14px 16px', color: 'white', fontWeight: '700', textAlign: 'center' }}>
                        {t.urgency}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        {getStatusBadge(t.status)}
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTicketId(t.id);
                          }}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            backgroundColor: 'rgba(79, 70, 229, 0.1)',
                            border: '1px solid rgba(79, 70, 229, 0.2)',
                            color: 'var(--primary-hover)',
                            fontSize: '11px',
                            fontWeight: '600',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <Eye size={12} />
                          Review
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* Ticket Detail Drawer Overlay */}
      {selectedTicketId && (
        <TicketDetail
          ticketId={selectedTicketId}
          onClose={() => setSelectedTicketId(null)}
          onUpdate={fetchDashboardData}
        />
      )}
      
    </div>
  );
};
