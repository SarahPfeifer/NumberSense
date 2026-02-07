import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function RegisterPage() {
  const [form, setForm] = useState({ first_name: '', last_name: '', username: '', password: '', role: 'teacher' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate('/teacher');
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
          <p className="text-muted">Create your teacher account</p>
        </div>

        <div className="card" style={{ marginTop: '1.5rem' }}>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
              <div className="form-group">
                <label>First Name</label>
                <input className="form-input" name="first_name" value={form.first_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input className="form-input" name="last_name" value={form.last_name} onChange={handleChange} required />
              </div>
            </div>
            <div className="form-group">
              <label>Username</label>
              <input className="form-input" name="username" value={form.username} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input className="form-input" type="password" name="password" value={form.password} onChange={handleChange} required minLength={6} />
            </div>

            {error && (
              <div style={{ padding: '.5rem .75rem', background: 'var(--ns-red-50)', color: 'var(--ns-red-600)', borderRadius: 'var(--ns-radius)', fontSize: '.875rem', marginBottom: '.75rem' }}>
                {error}
              </div>
            )}

            <button className="btn btn-primary btn-lg" type="submit" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm mt-2" style={{ color: 'var(--ns-gray-500)' }}>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
