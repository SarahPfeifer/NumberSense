import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    if (!code) {
      setError('No authorization code received from Google.');
      return;
    }

    api.googleOAuthCallback(code)
      .then(() => {
        navigate('/teacher', { replace: true });
      })
      .catch(err => {
        setError(err.message || 'Failed to connect Google Classroom.');
      });
  }, [searchParams, navigate]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--ns-gray-50)' }}>
      <div className="card" style={{ maxWidth: 420, textAlign: 'center', padding: '2rem' }}>
        {error ? (
          <>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ns-red-600)' }}>Connection Failed</h2>
            <p className="text-muted mt-1">{error}</p>
            <button className="btn btn-primary mt-2" onClick={() => navigate('/teacher')}>
              Back to Dashboard
            </button>
          </>
        ) : (
          <>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ns-indigo-600)' }}>Connecting Google Classroom...</h2>
            <p className="text-muted mt-1">Please wait while we complete the connection.</p>
          </>
        )}
      </div>
    </div>
  );
}
