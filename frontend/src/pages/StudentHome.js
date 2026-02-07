import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import api from '../services/api';

const DOMAIN_COLORS = {
  fractions: { bg: '#EEF2FF', border: '#C7D2FE', color: '#4338CA' },
  integers: { bg: '#F0FDF4', border: '#BBF7D0', color: '#166534' },
  multiplication: { bg: '#FFF7ED', border: '#FED7AA', color: '#9A3412' },
};

export default function StudentHome() {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.myAssignments().then(setAssignments).finally(() => setLoading(false));
  }, []);

  const pending = assignments.filter(a => !a.is_completed);
  const completed = assignments.filter(a => a.is_completed);

  return (
    <>
      <Navbar />
      <div className="practice-container" style={{ maxWidth: 600 }}>
        <div className="text-center" style={{ marginBottom: '2rem', marginTop: '1rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Your Assignments</h1>
          <p className="text-muted text-sm">Complete each task assigned by your teacher.</p>
        </div>

        {loading ? (
          <p className="text-center text-muted">Loading...</p>
        ) : pending.length === 0 && completed.length === 0 ? (
          <div className="card text-center" style={{ padding: '3rem' }}>
            <p style={{ fontSize: '1.125rem', fontWeight: 600 }}>All done!</p>
            <p className="text-muted mt-1">No assignments right now. Check back later.</p>
          </div>
        ) : (
          <>
            {pending.map(a => {
              const dc = DOMAIN_COLORS[a.skill_domain] || { bg: '#F3F4F6', border: '#D1D5DB', color: '#374151' };
              return (
                <div
                  key={a.id}
                  className="card"
                  style={{
                    marginBottom: '1rem', cursor: 'pointer',
                    border: `2px solid ${dc.border}`, background: dc.bg,
                    transition: 'transform .1s',
                  }}
                  onClick={() => navigate(`/student/practice/${a.id}`)}
                  onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                  onMouseOut={e => e.currentTarget.style.transform = 'none'}
                >
                  <div style={{ fontWeight: 700, fontSize: '1.125rem', color: dc.color }}>
                    {a.skill_name}
                  </div>
                  <div className="text-sm" style={{ marginTop: '.25rem', color: dc.color, opacity: .7 }}>
                    {a.skill_domain} &middot; {a.problem_type.replace(/_/g, ' ')}
                  </div>
                  <div style={{ marginTop: '.75rem' }}>
                    <span className="btn btn-primary" style={{ pointerEvents: 'none' }}>Start Practice</span>
                  </div>
                </div>
              );
            })}

            {completed.length > 0 && (
              <>
                <h3 className="text-sm text-muted" style={{ marginTop: '1.5rem', marginBottom: '.75rem' }}>Completed</h3>
                {completed.map(a => (
                  <div key={a.id} className="card" style={{ marginBottom: '.75rem', opacity: .7 }}>
                    <div className="flex-between">
                      <div>
                        <div style={{ fontWeight: 600 }}>{a.skill_name}</div>
                        <div className="text-sm text-muted">{a.skill_domain}</div>
                      </div>
                      <span className="badge badge-green">Done</span>
                    </div>
                    <button className="btn btn-secondary mt-1" style={{ fontSize: '.8125rem' }}
                      onClick={(e) => { e.stopPropagation(); navigate(`/student/practice/${a.id}`); }}>
                      Practice Again
                    </button>
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}
