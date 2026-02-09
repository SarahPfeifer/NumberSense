import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    const code = searchParams.get('code');
    if (!code) {
      setError('No authorization code received from Google.');
      return;
    }

    api.googleOAuthCallback(code)
      .then(data => {
        setResult(data);
      })
      .catch(err => {
        setError(err.message || 'Failed to connect Google Classroom.');
      });
  }, [searchParams, navigate]);

  const imported = result?.imported_courses?.filter(c => c.status === 'imported') || [];
  const existing = result?.imported_courses?.filter(c => c.status === 'already_imported') || [];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--ns-gray-50)' }}>
      <div className="card" style={{ maxWidth: 480, width: '100%', textAlign: 'center', padding: '2rem' }}>
        {error ? (
          <>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ns-red-600)' }}>Connection Failed</h2>
            <p className="text-muted mt-1">{error}</p>
            <button className="btn btn-primary mt-2" onClick={() => navigate('/teacher')}>
              Back to Dashboard
            </button>
          </>
        ) : result ? (
          <>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#E8F5E9', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto .75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>&#10003;</span>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ns-green-600)' }}>
              Google Classroom Connected
            </h2>
            <p className="text-sm text-muted mt-1">
              Signed in as {result.google_email}
            </p>

            {imported.length > 0 && (
              <div style={{ marginTop: '1.25rem', textAlign: 'left' }}>
                <p style={{ fontWeight: 600, fontSize: '.875rem', marginBottom: '.5rem' }}>
                  Imported {imported.length} class{imported.length !== 1 ? 'es' : ''}:
                </p>
                {imported.map(c => (
                  <div key={c.id} style={{
                    padding: '.5rem .75rem', background: '#F0FDF4', borderRadius: 'var(--ns-radius)',
                    marginBottom: '.375rem', fontSize: '.875rem',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div>
                      <span style={{ fontWeight: 500 }}>{c.name}</span>
                      <span className="text-muted" style={{ marginLeft: '.5rem', fontSize: '.8rem' }}>
                        {c.student_count} student{c.student_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <span className="badge badge-indigo">{c.class_code}</span>
                  </div>
                ))}
              </div>
            )}

            {existing.length > 0 && (
              <div style={{ marginTop: '.75rem', textAlign: 'left' }}>
                <p className="text-sm text-muted" style={{ marginBottom: '.5rem' }}>
                  {existing.length} class{existing.length !== 1 ? 'es' : ''} already in NumberSense
                  {existing.some(c => c.new_students > 0) ? ' (rosters synced)' : ''}:
                </p>
                {existing.map(c => (
                  <div key={c.id} style={{
                    padding: '.5rem .75rem', background: 'var(--ns-gray-100)', borderRadius: 'var(--ns-radius)',
                    marginBottom: '.375rem', fontSize: '.875rem',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div>
                      <span style={{ fontWeight: 500 }}>{c.name}</span>
                      <span className="text-muted" style={{ marginLeft: '.5rem', fontSize: '.8rem' }}>
                        {c.student_count} student{c.student_count !== 1 ? 's' : ''}
                        {c.new_students > 0 ? ` (+${c.new_students} new)` : ''}
                      </span>
                    </div>
                    <span className="badge badge-indigo">{c.class_code}</span>
                  </div>
                ))}
              </div>
            )}

            {(result.imported_courses || []).length === 0 && (
              <p className="text-sm text-muted" style={{ marginTop: '.75rem' }}>
                No active courses found in Google Classroom.
              </p>
            )}

            <button className="btn btn-primary mt-2" onClick={() => navigate('/teacher')}
              style={{ width: '100%' }}>
              Go to Dashboard
            </button>
          </>
        ) : (
          <>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ns-indigo-600)' }}>
              Connecting Google Classroom...
            </h2>
            <p className="text-muted mt-1">Importing your courses and student rosters. This may take a moment.</p>
          </>
        )}
      </div>
    </div>
  );
}
