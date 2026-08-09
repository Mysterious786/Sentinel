import React, { useState, useEffect } from 'react';
import { Shield, Activity, AlertTriangle, Eye, Clock, Globe } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchRecentEvents();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchRecentEvents();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard`);
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      
      const data = await response.json();
      setDashboardData(data.data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
      // Use mock data for demo if API not available
      setDashboardData(getMockDashboardData());
    }
  };

  const fetchRecentEvents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/events?hours=24&limit=10`);
      if (!response.ok) throw new Error('Failed to fetch events');
      
      const data = await response.json();
      setRecentEvents(data.events || []);
    } catch (err) {
      console.error('Failed to fetch events:', err);
      // Use mock data for demo
      setRecentEvents(getMockEvents());
    }
  };

  const simulateEvent = async (eventType = 'suspicious') => {
    try {
      const eventData = {
        event_type: 'authentication',
        action: 'login_attempt',
        source_ip: eventType === 'suspicious' ? '203.0.113.15' : '192.168.1.100',
        username: 'demo_user',
        timestamp: new Date().toISOString(),
        auth: {
          success: eventType !== 'suspicious',
          method: 'password'
        }
      };

      const response = await fetch(`${API_BASE_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_data: eventData })
      });

      if (response.ok) {
        // Refresh data after simulation
        setTimeout(() => {
          fetchDashboardData();
          fetchRecentEvents();
        }, 1000);
      }
    } catch (err) {
      console.error('Failed to simulate event:', err);
    }
  };

  const getMockDashboardData = () => ({
    statistics: {
      total_events_24h: 1247,
      high_threat_events: 23,
      average_threat_score: 2.8,
      blocked_ips_count: 5
    },
    agent_status: 'active',
    recent_decisions: []
  });

  const getMockEvents = () => [
    {
      decision_id: '1',
      threat_score: 8.5,
      reasoning: 'Suspicious IP with history of failed authentication attempts from foreign country',
      action_taken: 'block_ip',
      created_at: new Date().toISOString(),
      event_type: 'authentication',
      source_ip: '203.0.113.15',
      username: 'alice.johnson'
    },
    {
      decision_id: '2',
      threat_score: 2.1,
      reasoning: 'Normal user behavior pattern',
      action_taken: 'monitor',
      created_at: new Date(Date.now() - 300000).toISOString(),
      event_type: 'web_request',
      source_ip: '192.168.1.100',
      username: 'bob.smith'
    }
  ];

  const getThreatColor = (score) => {
    if (score >= 7) return '#ef4444';
    if (score >= 4) return '#f59e0b';
    return '#10b981';
  };

  const getActionBadgeColor = (action) => {
    switch (action) {
      case 'block_ip':
      case 'block_user':
        return '#ef4444';
      case 'alert':
      case 'escalate':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Shield className="loading-icon" />
        <p>Initializing Sentinel...</p>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Shield size={32} />
            <h1>Sentinel</h1>
            <span className="tagline">Persistent Threat Hunter</span>
          </div>
          <div className="status-indicator">
            <div className={`status-dot ${dashboardData?.agent_status}`}></div>
            <span>Agent Status: {dashboardData?.agent_status || 'Unknown'}</span>
          </div>
        </div>
      </header>

      <main className="dashboard">
        {/* Statistics Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <Activity size={20} />
              <span>Events (24h)</span>
            </div>
            <div className="stat-value">
              {dashboardData?.statistics?.total_events_24h || 0}
            </div>
          </div>
          
          <div className="stat-card threat">
            <div className="stat-header">
              <AlertTriangle size={20} />
              <span>High Threat Events</span>
            </div>
            <div className="stat-value">
              {dashboardData?.statistics?.high_threat_events || 0}
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-header">
              <Eye size={20} />
              <span>Avg Threat Score</span>
            </div>
            <div className="stat-value">
              {dashboardData?.statistics?.average_threat_score || 0}
            </div>
          </div>
          
          <div className="stat-card blocked">
            <div className="stat-header">
              <Globe size={20} />
              <span>Blocked IPs</span>
            </div>
            <div className="stat-value">
              {dashboardData?.statistics?.blocked_ips_count || 0}
            </div>
          </div>
        </div>

        {/* Demo Controls */}
        <div className="demo-controls">
          <h3>🎭 Demo Controls</h3>
          <div className="demo-buttons">
            <button 
              className="demo-btn suspicious"
              onClick={() => simulateEvent('suspicious')}
            >
              Simulate Suspicious Event
            </button>
            <button 
              className="demo-btn normal"
              onClick={() => simulateEvent('normal')}
            >
              Simulate Normal Event
            </button>
          </div>
        </div>

        {/* Recent Events */}
        <div className="events-section">
          <h2>🔍 Recent Threat Analysis</h2>
          <div className="events-list">
            {recentEvents.length === 0 ? (
              <div className="no-events">
                <p>No recent events. Try simulating some events above!</p>
              </div>
            ) : (
              recentEvents.map((event) => (
                <div key={event.decision_id} className="event-card">
                  <div className="event-header">
                    <div className="event-meta">
                      <span className="event-type">{event.event_type}</span>
                      <span className="event-time">
                        <Clock size={14} />
                        {new Date(event.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="threat-score" style={{ color: getThreatColor(event.threat_score) }}>
                      {event.threat_score}/10
                    </div>
                  </div>
                  
                  <div className="event-details">
                    <div className="event-info">
                      <span><strong>User:</strong> {event.username}</span>
                      <span><strong>IP:</strong> {event.source_ip}</span>
                      <span 
                        className="action-badge"
                        style={{ backgroundColor: getActionBadgeColor(event.action_taken) }}
                      >
                        {event.action_taken}
                      </span>
                    </div>
                  </div>
                  
                  <div className="event-reasoning">
                    <p>{event.reasoning}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Key Features */}
        <div className="features-section">
          <h2>🧠 Memory-Driven Detection</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>Vector Memory</h3>
              <p>Every event is stored as a semantic vector in CockroachDB, enabling similarity search across months of history.</p>
            </div>
            <div className="feature-card">
              <h3>AI Reasoning</h3>
              <p>Claude analyzes events in context of historical patterns to identify coordinated attacks.</p>
            </div>
            <div className="feature-card">
              <h3>Autonomous Actions</h3>
              <p>Agent automatically blocks threats, alerts security teams, and learns from outcomes.</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>🛡️ Sentinel - The agent that remembers every byte, every login, every anomaly.</p>
        {error && <p className="error">Demo Mode: {error}</p>}
      </footer>
    </div>
  );
}

export default App;