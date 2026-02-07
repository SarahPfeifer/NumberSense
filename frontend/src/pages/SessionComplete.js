import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import api from '../services/api';

export default function SessionComplete() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSessionSummary(sessionId)
      .then(setSummary)
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="practice-container">
          <div className="practice-card">
            <p className="text-muted">Calculating your results...</p>
          </div>
        </div>
      </>
    );
  }

  if (!summary) {
    return (
      <>
        <Navbar />
        <div className="practice-container">
          <div className="practice-card">
            <p>Could not load summary.</p>
            <button className="btn btn-primary mt-2" onClick={() => navigate('/student')}>Back to Home</button>
          </div>
        </div>
      </>
    );
  }

  const accuracyColor = summary.accuracy_pct >= 85
    ? 'var(--ns-green-600)'
    : summary.accuracy_pct >= 60
      ? 'var(--ns-yellow-500)'
      : 'var(--ns-red-500)';

  return (
    <>
      <Navbar />
      <div className="practice-container">
        <div className="practice-card">
          <div style={{ fontSize: '2.5rem', marginBottom: '.5rem' }}>
            {summary.accuracy_pct >= 85 ? '★' : summary.accuracy_pct >= 60 ? '●' : '○'}
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '.25rem' }}>
            Practice Complete!
          </h2>
          <p style={{ color: 'var(--ns-gray-600)', fontSize: '1.0625rem', marginBottom: '2rem' }}>
            {summary.improvement_message}
          </p>

          {/* Stats */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem',
            padding: '1.5rem', background: 'var(--ns-gray-50)', borderRadius: 'var(--ns-radius-lg)',
            marginBottom: '2rem',
          }}>
            <div>
              <div className="text-sm text-muted">Accuracy</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: accuracyColor }}>
                {summary.accuracy_pct}%
              </div>
            </div>
            <div>
              <div className="text-sm text-muted">Correct</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>
                {summary.correct_count}/{summary.total_problems}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted">Avg Speed</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>
                {summary.avg_response_time_ms ? `${(summary.avg_response_time_ms / 1000).toFixed(1)}s` : '—'}
              </div>
            </div>
          </div>

          {summary.visual_support_trend === 'decreasing' && (
            <div style={{
              padding: '.75rem 1rem', background: 'var(--ns-green-50)',
              borderRadius: 'var(--ns-radius)', marginBottom: '1.5rem',
              color: 'var(--ns-green-600)', fontSize: '.875rem',
            }}>
              You're using fewer visual supports — your number sense is growing!
            </div>
          )}

          <button className="btn btn-primary btn-lg" onClick={() => navigate('/student')} style={{ minWidth: 200 }}>
            Back to Assignments
          </button>
        </div>
      </div>
    </>
  );
}
