import { useState, useEffect } from 'react'
import { AdminDashboard } from './components/AdminDashboard'
import { DummyWebsite } from './components/DummyWebsite'

function App() {
  const [view, setView] = useState<'dashboard' | 'website'>('dashboard')
  const [status, setStatus] = useState<'online' | 'offline' | 'loading'>('loading')
  const [agentName, setAgentName] = useState(() => {
    return localStorage.getItem('flowbot_agent_name') || 'Support Agent'
  })

  useEffect(() => {
    if (window.location.port === '5174') {
      setView('website')
    } else {
      setView('dashboard')
      
      // Request browser Notification permission
      if (typeof window !== 'undefined' && 'Notification' in window) {
        if (Notification.permission === 'default') {
          Notification.requestPermission()
        }
      }
    }
  }, [])

  useEffect(() => {
    if (view === 'website') return; // no need to check status on website port
    
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/status');
        if (response.ok) {
          const data = await response.json();
          setStatus(data.status);
        } else {
          setStatus('offline');
        }
      } catch (error) {
        console.error('Failed to check system status:', error);
        setStatus('offline');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [view]);

  const handleAgentNameChange = (name: string) => {
    setAgentName(name)
    localStorage.setItem('flowbot_agent_name', name)
  }

  if (view === 'website') {
    return <DummyWebsite />
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Admin Panel Header / Top bar */}
      <header
        style={{
          borderBottom: '1px solid var(--border-glass)',
          padding: '16px 32px',
          background: 'rgba(15, 23, 42, 0.4)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <span 
            style={{ 
              fontSize: '20px', 
              fontWeight: '800', 
              fontFamily: "'Outfit', sans-serif",
              letterSpacing: '-0.025em',
              background: 'linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            FlowBOT
          </span>
          
          <a
            href="http://localhost:5174"
            target="_blank"
            rel="noreferrer"
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              backgroundColor: 'rgba(14, 165, 233, 0.1)',
              border: '1px solid rgba(14, 165, 233, 0.2)',
              color: 'var(--secondary)',
              fontSize: '12px',
              fontWeight: '600',
              textDecoration: 'none',
              transition: 'background 0.2s'
            }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'rgba(14, 165, 233, 0.2)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'rgba(14, 165, 233, 0.1)')}
          >
            Open Demo Website
          </a>
        </div>
        
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          {/* Agent Name input */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '500' }}>
              Agent Name:
            </label>
            <input
              type="text"
              value={agentName}
              onChange={e => handleAgentNameChange(e.target.value)}
              placeholder="Your name"
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                backgroundColor: '#0c111e',
                border: '1px solid var(--border-glass)',
                color: 'white',
                fontSize: '12.5px',
                width: '140px'
              }}
            />
          </div>

          <div 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              fontSize: '12.5px', 
              fontWeight: '600',
              color: status === 'online' ? 'var(--success)' : status === 'offline' ? 'var(--danger)' : 'var(--text-muted)'
            }}
          >
            <span 
              style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                backgroundColor: status === 'online' ? 'var(--success)' : status === 'offline' ? 'var(--danger)' : 'var(--text-muted)',
                boxShadow: status === 'online' 
                  ? '0 0 8px rgba(16, 185, 129, 0.6)' 
                  : status === 'offline' 
                    ? '0 0 8px rgba(239, 68, 68, 0.6)' 
                    : 'none',
                transition: 'all 0.3s ease'
              }}
            ></span>
            {status === 'online' ? 'Online' : status === 'offline' ? 'Offline' : 'Checking...'}
          </div>
        </div>
      </header>

      {/* Main Admin Dashboard View */}
      <main style={{ flex: 1, display: 'flex' }}>
        <AdminDashboard />
      </main>
    </div>
  )
}

export default App
