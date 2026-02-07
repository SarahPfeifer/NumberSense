import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import api from '../services/api';

const DOMAIN_INFO = {
  fractions: { label: 'Fractions', color: '#6366F1', bg: '#EEF2FF' },
  integers: { label: 'Combining Integers', color: '#16A34A', bg: '#F0FDF4' },
  multiplication: { label: 'Multiplication Fluency', color: '#EA580C', bg: '#FFF7ED' },
};

export default function AssignSkill() {
  const { id: classroomId } = useParams();
  const navigate = useNavigate();
  const [skills, setSkills] = useState([]);
  const [selected, setSelected] = useState(null);
  const [visualSupports, setVisualSupports] = useState(true);
  const [timeLimit, setTimeLimit] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [classroom, setClassroom] = useState(null);

  useEffect(() => {
    api.listSkills().then(setSkills);
    api.getClassroom(classroomId).then(setClassroom);
  }, [classroomId]);

  const grouped = skills.reduce((acc, s) => {
    if (!acc[s.domain]) acc[s.domain] = [];
    acc[s.domain].push(s);
    return acc;
  }, {});

  const handleAssign = async () => {
    if (!selected) return;
    setSubmitting(true);
    try {
      await api.createAssignment({
        skill_id: selected.id,
        classroom_id: classroomId,
        visual_supports: visualSupports,
        time_limit_seconds: timeLimit ? parseInt(timeLimit) * 60 : null,
      });
      navigate(`/teacher/classroom/${classroomId}`);
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
        <p className="text-sm text-muted" style={{ cursor: 'pointer' }} onClick={() => navigate(`/teacher/classroom/${classroomId}`)}>
          &larr; Back to {classroom?.name || 'class'}
        </p>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginTop: '.5rem' }}>Assign a Skill</h1>
        <p className="text-muted text-sm mt-1">Select a skill and configure the assignment. One click to assign.</p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', marginTop: '1.5rem', alignItems: 'start' }}>
          {/* Skill Picker */}
          <div>
            {Object.entries(grouped).map(([domain, domainSkills]) => {
              const info = DOMAIN_INFO[domain] || { label: domain, color: '#6B7280', bg: '#F3F4F6' };
              return (
                <div key={domain} style={{ marginBottom: '1.5rem' }}>
                  <h3 style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '.75rem', color: info.color }}>
                    {info.label}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
                    {domainSkills.map(skill => (
                      <div
                        key={skill.id}
                        className="card"
                        onClick={() => setSelected(skill)}
                        style={{
                          cursor: 'pointer', padding: '1rem 1.25rem',
                          border: selected?.id === skill.id ? `2px solid ${info.color}` : '2px solid transparent',
                          background: selected?.id === skill.id ? info.bg : 'var(--ns-white)',
                          transition: 'all .15s',
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: '.9375rem' }}>{skill.name}</div>
                        {skill.description && (
                          <p className="text-sm text-muted" style={{ marginTop: '.25rem' }}>{skill.description}</p>
                        )}
                        <div className="flex gap-1 mt-1">
                          <span className="badge badge-gray">Grade {skill.grade_level}</span>
                          <span className="badge badge-gray">{skill.problem_type.replace(/_/g, ' ')}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Settings Panel */}
          <div className="card" style={{ position: 'sticky', top: 72 }}>
            <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Assignment Settings</h3>

            {selected ? (
              <>
                <div style={{ padding: '.75rem', background: 'var(--ns-indigo-50)', borderRadius: 'var(--ns-radius)', marginBottom: '1rem' }}>
                  <div style={{ fontWeight: 600, color: 'var(--ns-indigo-700)' }}>{selected.name}</div>
                  <div className="text-sm text-muted">{selected.domain}</div>
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem', cursor: 'pointer' }}>
                    <input type="checkbox" checked={visualSupports} onChange={e => setVisualSupports(e.target.checked)} />
                    Visual supports enabled
                  </label>
                  <p className="text-sm text-muted" style={{ marginTop: '.25rem' }}>
                    Number lines, fraction bars, and models will be shown to support understanding.
                  </p>
                </div>

                <div className="form-group">
                  <label>Time limit (minutes, optional)</label>
                  <input className="form-input" type="number" min="1" max="30" value={timeLimit} onChange={e => setTimeLimit(e.target.value)} placeholder="No limit" />
                </div>

                <button className="btn btn-primary btn-lg" style={{ width: '100%' }} onClick={handleAssign} disabled={submitting}>
                  {submitting ? 'Assigning...' : 'Assign to Class'}
                </button>
              </>
            ) : (
              <p className="text-muted text-sm">Select a skill from the left to configure your assignment.</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
