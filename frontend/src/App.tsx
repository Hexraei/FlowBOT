import { useState, useEffect } from 'react'
import { AdminDashboard } from './components/AdminDashboard'
import { ChatWidget } from './components/ChatWidget'

function App() {
  const [status, setStatus] = useState<'online' | 'offline' | 'loading'>('loading')

  useEffect(() => {
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
  }, []);

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
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
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
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

      {/* Visitor Chat Widget Overlay */}
      <ChatWidget />
    </div>
  )
}

export default App
