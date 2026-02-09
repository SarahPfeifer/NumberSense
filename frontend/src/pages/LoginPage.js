import React, { useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const [mode, setMode] = useState('teacher'); // 'teacher' | 'student'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [classCode, setClassCode] = useState('');
  const [studentId, setStudentId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, classCodeLogin } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // If there's a redirect param (e.g., from Classroom deep link), go there after login
  const redirectTo = searchParams.get('redirect');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'teacher') {
        const user = await login(username, password);
        navigate(redirectTo ? decodeURIComponent(redirectTo) : (user.role === 'teacher' ? '/teacher' : '/student'));
      } else {
        await classCodeLogin(classCode, studentId);
        navigate(redirectTo ? decodeURIComponent(redirectTo) : '/student');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--ns-gray-50)' }}>
      <div style={{ width: '100%', maxWidth: 420, padding: '0 1rem' }}>
        <div className="text-center mb-2">
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ns-indigo-600)' }}>NumberSense</h1>
          <p className="text-muted" style={{ marginTop: 4 }}>Making math fast, flexible, and intuitive</p>
        </div>

        <div className="card" style={{ marginTop: '1.5rem' }}>
          {/* Mode Tabs */}
          <div style={{ display: 'flex', marginBottom: '1.5rem', borderBottom: '2px solid var(--ns-gray-200)' }}>
            <button
              onClick={() => { setMode('teacher'); setError(''); }}
              style={{
                flex: 1, padding: '.75rem', border: 'none', background: 'none',
                fontWeight: 600, fontSize: '.875rem', cursor: 'pointer', fontFamily: 'var(--ns-font)',
                borderBottom: mode === 'teacher' ? '2px solid var(--ns-indigo-600)' : '2px solid transparent',
                color: mode === 'teacher' ? 'var(--ns-indigo-600)' : 'var(--ns-gray-500)',
                marginBottom: -2,
              }}
            >
              Teacher Login
            </button>
            <button
              onClick={() => { setMode('student'); setError(''); }}
              style={{
                flex: 1, padding: '.75rem', border: 'none', background: 'none',
                fontWeight: 600, fontSize: '.875rem', cursor: 'pointer', fontFamily: 'var(--ns-font)',
                borderBottom: mode === 'student' ? '2px solid var(--ns-indigo-600)' : '2px solid transparent',
                color: mode === 'student' ? 'var(--ns-indigo-600)' : 'var(--ns-gray-500)',
                marginBottom: -2,
              }}
            >
              Student Login
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {mode === 'teacher' ? (
              <>
                <div className="form-group">
                  <label>Username</label>
                  <input className="form-input" value={username} onChange={e => setUsername(e.target.value)} placeholder="demo.teacher" required />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="teacher123" required />
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label>Class Code</label>
                  <input className="form-input" value={classCode} onChange={e => setClassCode(e.target.value)} placeholder="DEMO01" required style={{ textTransform: 'uppercase', letterSpacing: '.1em', fontWeight: 600 }} />
                </div>
                <div className="form-group">
                  <label>Your Name</label>
                  <input className="form-input" value={studentId} onChange={e => setStudentId(e.target.value)} placeholder="Alex J" required />
                </div>
              </>
            )}

            {error && (
              <div style={{ padding: '.5rem .75rem', background: 'var(--ns-red-50)', color: 'var(--ns-red-600)', borderRadius: 'var(--ns-radius)', fontSize: '.875rem', marginBottom: '.75rem' }}>
                {error}
              </div>
            )}

            <button className="btn btn-primary btn-lg" type="submit" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {mode === 'teacher' && (
            <p className="text-center text-sm mt-2" style={{ color: 'var(--ns-gray-500)' }}>
              New teacher? <Link to="/register">Create an account</Link>
            </p>
          )}
        </div>

        <p className="text-center text-sm mt-2" style={{ color: 'var(--ns-gray-400)' }}>
          Demo: teacher = demo.teacher / teacher123
        </p>
      </div>
    </div>
  );
}
