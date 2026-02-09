import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

export default function SharedAssignment() {
  const { shareToken } = useParams();
  const navigate = useNavigate();
  const { claimSession } = useAuth();
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState('');

  const API_BASE = process.env.REACT_APP_API_URL || '/api';

  useEffect(() => {
    fetch(`${API_BASE}/shared/${shareToken}`)
      .then(res => {
        if (!res.ok) throw new Error('Assignment not found');
        return res.json();
      })
      .then(setInfo)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [shareToken]);

  const handlePickStudent = async (studentId) => {
    setClaiming(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/shared/${shareToken}/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to start' }));
        throw new Error(err.detail);
      }
      const data = await res.json();

      // Authenticate via context so ProtectedRoute allows access
      const nameParts = data.student_name.split(' ');
      claimSession(data.access_token, {
        id: studentId,
        first_name: nameParts[0],
        last_name: nameParts.slice(1).join(' '),
        role: 'student',
      });

      // Go straight into the practice session
      navigate(`/student/practice/${data.assignment_id}`);
    } catch (err) {
      setError(err.message);
      setClaiming(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.wrapper}>
        <div style={styles.card}>
          <div style={styles.logo}>NumberSense</div>
          <p style={{ color: '#6B7280' }}>Loading assignment...</p>
        </div>
      </div>
    );
  }

  if (error && !info) {
    return (
      <div style={styles.wrapper}>
        <div style={styles.card}>
          <div style={styles.logo}>NumberSense</div>
          <p style={{ color: '#EF4444', marginTop: '1rem' }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        <div style={styles.logo}>NumberSense</div>

        <div style={styles.skillBadge}>
          {info.skill_domain}
        </div>
        <h1 style={styles.title}>{info.title}</h1>
        <p style={styles.className}>{info.class_name}</p>

        <div style={styles.divider} />

        <p style={styles.instruction}>Select your name to begin:</p>

        {error && <p style={{ color: '#EF4444', fontSize: '.875rem', marginBottom: '.75rem' }}>{error}</p>}

        <div style={styles.studentList}>
          {info.students.map(s => (
            <button
              key={s.id}
              onClick={() => handlePickStudent(s.id)}
              disabled={claiming}
              style={styles.studentBtn}
              onMouseOver={e => {
                e.currentTarget.style.background = '#EEF2FF';
                e.currentTarget.style.borderColor = '#6366F1';
              }}
              onMouseOut={e => {
                e.currentTarget.style.background = '#fff';
                e.currentTarget.style.borderColor = '#E5E7EB';
              }}
            >
              <span style={styles.avatar}>
                {s.name.charAt(0).toUpperCase()}
              </span>
              <span style={styles.studentName}>{s.name}</span>
              <span style={styles.arrow}>&rsaquo;</span>
            </button>
          ))}
        </div>

        {info.students.length === 0 && (
          <p style={{ color: '#6B7280', fontSize: '.875rem', textAlign: 'center', marginTop: '1rem' }}>
            No students enrolled in this class yet.
          </p>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #EEF2FF 0%, #F9FAFB 100%)',
    padding: '1rem',
  },
  card: {
    background: '#fff',
    borderRadius: '16px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
    padding: '2rem',
    maxWidth: 440,
    width: '100%',
    textAlign: 'center',
  },
  logo: {
    fontSize: '1.25rem',
    fontWeight: 800,
    color: '#4F46E5',
    letterSpacing: '-0.02em',
    marginBottom: '1.25rem',
  },
  skillBadge: {
    display: 'inline-block',
    background: '#EEF2FF',
    color: '#4F46E5',
    fontSize: '.75rem',
    fontWeight: 600,
    padding: '.25rem .75rem',
    borderRadius: '999px',
    textTransform: 'uppercase',
    letterSpacing: '.04em',
    marginBottom: '.5rem',
  },
  title: {
    fontSize: '1.375rem',
    fontWeight: 700,
    color: '#111827',
    margin: '0 0 .25rem',
  },
  className: {
    fontSize: '.875rem',
    color: '#6B7280',
    margin: 0,
  },
  divider: {
    height: 1,
    background: '#E5E7EB',
    margin: '1.25rem 0',
  },
  instruction: {
    fontSize: '.9375rem',
    fontWeight: 600,
    color: '#374151',
    marginBottom: '1rem',
  },
  studentList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '.5rem',
    maxHeight: '50vh',
    overflowY: 'auto',
  },
  studentBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '.75rem',
    padding: '.75rem 1rem',
    background: '#fff',
    border: '1.5px solid #E5E7EB',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all .15s',
    textAlign: 'left',
    width: '100%',
    fontSize: '1rem',
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: '50%',
    background: '#EEF2FF',
    color: '#4F46E5',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: '.875rem',
    flexShrink: 0,
  },
  studentName: {
    fontWeight: 500,
    color: '#111827',
    flex: 1,
  },
  arrow: {
    fontSize: '1.5rem',
    color: '#9CA3AF',
    fontWeight: 300,
  },
};
