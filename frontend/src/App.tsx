import { AdminDashboard } from './components/AdminDashboard'
import { ChatWidget } from './components/ChatWidget'

function App() {
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
          <div
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)',
              fontWeight: '800',
              fontSize: '14px',
              color: 'white',
              letterSpacing: '0.05em'
            }}
          >
            FLOWZINT
          </div>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: '600' }}>| Operations Console</span>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            System Integrity: <span style={{ color: 'var(--success)', fontWeight: '700' }}>Stable</span>
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
