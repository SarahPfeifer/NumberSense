import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import api from '../services/api';

export default function TeacherDashboard() {
  const [classrooms, setClassrooms] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(true);
  const [googleStatus, setGoogleStatus] = useState(null);
  const [googleLoading, setGoogleLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.listClassrooms().then(setClassrooms).finally(() => setLoading(false));
    api.googleStatus().then(setGoogleStatus).catch(() => {});
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    const c = await api.createClassroom(newName.trim());
    setClassrooms([c, ...classrooms]);
    setNewName('');
    setShowCreate(false);
  };

  const handleConnectGoogle = async () => {
    setGoogleLoading(true);
    try {
      const { redirect_url } = await api.googleOAuthUrl();
      window.location.href = redirect_url;
    } catch (err) {
      alert('Could not start Google Classroom connection. Please try again.');
      setGoogleLoading(false);
    }
  };

  const handleDisconnectGoogle = async () => {
    if (!window.confirm('Disconnect Google Classroom? Existing posted assignments will remain in Classroom.')) return;
    setGoogleLoading(true);
    try {
      await api.googleDisconnect();
      setGoogleStatus({ connected: false });
    } catch (err) {
      alert('Failed to disconnect. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
        <div className="flex-between">
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>My Classes</h1>
            <p className="text-sm text-muted mt-1">Manage your classes, assign skills, and track student progress.</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
            + New Class
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="card mt-2" style={{ display: 'flex', gap: '.75rem', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Class Name</label>
              <input className="form-input" value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. 4th Grade Math — Period 1" autoFocus />
            </div>
            <button className="btn btn-primary" type="submit">Create</button>
            <button className="btn btn-secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
          </form>
        )}

        {/* Google Classroom Connection */}
        {googleStatus && (
          <div className="card" style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" fill="#4285F4"/></svg>
              <div>
                <div style={{ fontWeight: 600, fontSize: '.9375rem' }}>Google Classroom</div>
                {googleStatus.connected ? (
                  <div className="text-sm" style={{ color: 'var(--ns-green-600)' }}>
                    Connected as {googleStatus.google_email}
                  </div>
                ) : (
                  <div className="text-sm text-muted">Not connected — link your account to post assignments to Classroom</div>
                )}
              </div>
            </div>
            {googleStatus.connected ? (
              <button className="btn btn-secondary" onClick={handleDisconnectGoogle} disabled={googleLoading}
                style={{ fontSize: '.8125rem', whiteSpace: 'nowrap' }}>
                Disconnect
              </button>
            ) : (
              <button className="btn btn-primary" onClick={handleConnectGoogle} disabled={googleLoading}
                style={{ whiteSpace: 'nowrap' }}>
                {googleLoading ? 'Connecting...' : 'Connect Google Classroom'}
              </button>
            )}
          </div>
        )}

        {loading ? (
          <p className="text-center text-muted mt-3">Loading classes...</p>
        ) : classrooms.length === 0 ? (
          <div className="card text-center mt-3" style={{ padding: '3rem' }}>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--ns-gray-700)' }}>No classes yet</p>
            <p className="text-muted mt-1">Create your first class to get started.</p>
          </div>
        ) : (
          <div className="grid-2 mt-2">
            {classrooms.map(c => (
              <div
                key={c.id}
                className="card"
                style={{ cursor: 'pointer', transition: 'box-shadow .15s' }}
                onClick={() => navigate(`/teacher/classroom/${c.id}`)}
                onMouseOver={e => e.currentTarget.style.boxShadow = 'var(--ns-shadow-md)'}
                onMouseOut={e => e.currentTarget.style.boxShadow = 'var(--ns-shadow)'}
              >
                <div className="flex-between">
                  <h3 style={{ fontSize: '1.0625rem', fontWeight: 600 }}>{c.name}</h3>
                  <span className="badge badge-indigo">{c.class_code}</span>
                </div>
                <p className="text-sm text-muted mt-1">
                  {c.student_count} student{c.student_count !== 1 ? 's' : ''}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
