import React from 'react';
import { ChatWidget } from './ChatWidget';
import { Cpu, Globe, Rocket, CheckCircle } from 'lucide-react';

export const DummyWebsite: React.FC = () => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#070a13', 
      color: '#e2e8f0', 
      fontFamily: "'Inter', sans-serif",
      position: 'relative',
      overflowX: 'hidden'
    }}>
      {/* Dynamic BG effects */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        left: '20%',
        width: '600px',
        height: '600px',
        background: 'radial-gradient(circle, rgba(79, 70, 229, 0.12) 0%, rgba(0,0,0,0) 70%)',
        zIndex: 0,
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute',
        top: '40%',
        right: '-10%',
        width: '500px',
        height: '500px',
        background: 'radial-gradient(circle, rgba(14, 165, 233, 0.1) 0%, rgba(0,0,0,0) 70%)',
        zIndex: 0,
        pointerEvents: 'none'
      }} />

      {/* Navigation Header */}
      <nav style={{
        padding: '24px 64px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(7, 10, 19, 0.7)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(79, 70, 229, 0.3)'
          }}>
            <Rocket size={18} color="white" />
          </div>
          <span style={{ fontSize: '20px', fontWeight: '800', fontFamily: "'Outfit', sans-serif", letterSpacing: '-0.02em', color: 'white' }}>
            FlowZint
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '32px', fontSize: '14px', fontWeight: '500', color: '#94a3b8' }}>
          <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='white'} onMouseLeave={e => e.currentTarget.style.color='#94a3b8'}>Home</span>
          <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='white'} onMouseLeave={e => e.currentTarget.style.color='#94a3b8'}>AI Solutions</span>
          <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='white'} onMouseLeave={e => e.currentTarget.style.color='#94a3b8'}>Internships</span>
          <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='white'} onMouseLeave={e => e.currentTarget.style.color='#94a3b8'}>Careers</span>
          <span style={{ cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={e => e.currentTarget.style.color='white'} onMouseLeave={e => e.currentTarget.style.color='#94a3b8'}>Contact</span>
        </div>
        
        <button style={{
          padding: '10px 20px',
          borderRadius: '8px',
          backgroundColor: '#4f46e5',
          border: 'none',
          color: 'white',
          fontSize: '13.5px',
          fontWeight: '600',
          boxShadow: '0 4px 12px rgba(79, 70, 229, 0.2)'
        }}
        onMouseEnter={e => e.currentTarget.style.backgroundColor='#6366f1'}
        onMouseLeave={e => e.currentTarget.style.backgroundColor='#4f46e5'}
        >
          Get Started
        </button>
      </nav>

      {/* Main Container */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '64px 24px', display: 'flex', flexDirection: 'column', gap: '96px', zIndex: 1, position: 'relative' }}>
        
        {/* Hero Section */}
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px', maxWidth: '800px', margin: '0 auto' }}>
          <span style={{ 
            padding: '6px 14px', 
            borderRadius: '20px', 
            fontSize: '11px', 
            fontWeight: '700', 
            backgroundColor: 'rgba(79, 70, 229, 0.1)', 
            border: '1px solid rgba(79, 70, 229, 0.2)', 
            color: '#818cf8', 
            letterSpacing: '0.05em', 
            textTransform: 'uppercase' 
          }}>
            Next-Gen Enterprise AI
          </span>
          <h1 style={{ fontSize: '56px', fontWeight: '800', lineHeight: '1.1', fontFamily: "'Outfit', sans-serif", letterSpacing: '-0.03em', color: 'white' }}>
            Transforming Operations with <span style={{ background: 'linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Autonomous Intelligence</span>
          </h1>
          <p style={{ fontSize: '18px', color: '#94a3b8', lineHeight: '1.6', maxWidth: '640px' }}>
            FlowZint designs and deploys secure, scalable SaaS applications, web infrastructure, and AI-driven automation pipelines for modern enterprises.
          </p>
          <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
            <button style={{ padding: '14px 28px', borderRadius: '10px', backgroundColor: '#4f46e5', border: 'none', color: 'white', fontSize: '15px', fontWeight: '600', boxShadow: '0 4px 16px rgba(79, 70, 229, 0.3)' }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor='#6366f1'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor='#4f46e5'}
            >
              Explore AI Services
            </button>
            <button style={{ padding: '14px 28px', borderRadius: '10px', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', color: 'white', fontSize: '15px', fontWeight: '600' }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor='rgba(255,255,255,0.06)'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor='rgba(255,255,255,0.03)'}
            >
              Contact Sales
            </button>
          </div>
        </div>

        {/* Services Section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ fontSize: '32px', fontWeight: '800', fontFamily: "'Outfit', sans-serif", color: 'white' }}>Our Tech Infrastructure Capabilities</h2>
            <p style={{ color: '#94a3b8', fontSize: '15px', marginTop: '8px' }}>Engineered for performance, speed, and high-level cybersecurity.</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid var(--border-glass)' }}>
              <div style={{ padding: '12px', borderRadius: '10px', backgroundColor: 'rgba(79, 70, 229, 0.1)', color: '#818cf8', width: 'fit-content' }}>
                <Cpu size={24} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'white' }}>AI Automation Pipelines</h3>
              <p style={{ fontSize: '13.5px', color: '#94a3b8', lineHeight: '1.5' }}>
                Automate complex reasoning, document extraction, and workflow routing using custom fine-tuned LLMs and semantic vector search indexes.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid var(--border-glass)' }}>
              <div style={{ padding: '12px', borderRadius: '10px', backgroundColor: 'rgba(14, 165, 233, 0.1)', color: '#38bdf8', width: 'fit-content' }}>
                <Globe size={24} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'white' }}>Scalable SaaS Systems</h3>
              <p style={{ fontSize: '13.5px', color: '#94a3b8', lineHeight: '1.5' }}>
                Full-stack cloud-native applications featuring robust multi-tenant security, dashboard visualizations, and live event webhooks.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid var(--border-glass)' }}>
              <div style={{ padding: '12px', borderRadius: '10px', backgroundColor: 'rgba(217, 70, 239, 0.1)', color: '#f472b6', width: 'fit-content' }}>
                <Rocket size={24} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'white' }}>Web Infrastructure</h3>
              <p style={{ fontSize: '13.5px', color: '#94a3b8', lineHeight: '1.5' }}>
                High-speed deployments with load balancing, reverse proxy configurations, edge caching, and automated HTTPS certificate provisioning.
              </p>
            </div>
          </div>
        </div>

        {/* Careers & Internships Section */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '64px', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <span style={{ color: '#0ea5e9', fontSize: '12px', fontWeight: '700', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Join Our Vision</span>
            <h2 style={{ fontSize: '38px', fontWeight: '800', fontFamily: "'Outfit', sans-serif", color: 'white', lineHeight: '1.2' }}>
              Accelerate Your Career in AI Engineering
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14.5px', lineHeight: '1.6' }}>
              We run intensive training academies and internship programs designed to introduce students to professional web development, system architecture, and machine learning deployments.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: '#cbd5e1' }}>
                <CheckCircle size={16} color="var(--success)" />
                <span>One-on-One Mentorship from Tech Architects</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: '#cbd5e1' }}>
                <CheckCircle size={16} color="var(--success)" />
                <span>Hands-on experience with production systems</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: '#cbd5e1' }}>
                <CheckCircle size={16} color="var(--success)" />
                <span>Job placement opportunities post graduation</span>
              </div>
            </div>
          </div>

          {/* Internship Pricing Card */}
          <div className="glass-panel" style={{ 
            padding: '40px', 
            border: '1px solid rgba(79, 70, 229, 0.25)', 
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(79, 70, 229, 0.05) 100%)',
            boxShadow: '0 8px 32px rgba(79, 70, 229, 0.1)'
          }}>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: 'white' }}>AI & Web Dev Internship</h3>
            <p style={{ fontSize: '12.5px', color: '#94a3b8', marginTop: '4px' }}>Standard intake enrollment</p>
            
            <div style={{ margin: '24px 0', borderTop: '1px solid rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.05)', padding: '20px 0' }}>
              <span style={{ fontSize: '36px', fontWeight: '800', color: 'white' }}>Rs. 1,999</span>
              <span style={{ fontSize: '13px', color: '#94a3b8' }}> / one-time registration</span>
            </div>
            
            <ul style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: '#cbd5e1', listStyleType: 'none', padding: 0 }}>
              <li style={{ display: 'flex', gap: '8px' }}>• Full Curriculum access (React + Python APIs)</li>
              <li style={{ display: 'flex', gap: '8px' }}>• Weekly live code reviews & assessments</li>
              <li style={{ display: 'flex', gap: '8px' }}>• Certificate of Excellence on project submission</li>
            </ul>
            
            <button style={{ 
              width: '100%', 
              padding: '14px', 
              borderRadius: '8px', 
              backgroundColor: '#4f46e5', 
              border: 'none', 
              color: 'white', 
              fontSize: '14px', 
              fontWeight: '700', 
              marginTop: '32px',
              boxShadow: '0 4px 12px rgba(79, 70, 229, 0.25)'
            }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor='#6366f1'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor='#4f46e5'}
            >
              Enroll Now
            </button>
          </div>
        </div>

      </div>

      {/* Floating Chat Widget Overlay */}
      <ChatWidget />
    </div>
  );
};
