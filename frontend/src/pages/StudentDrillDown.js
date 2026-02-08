import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import api from '../services/api';

const FLUENCY_COLORS = {
  fluent: 'badge-green',
  progressing: 'badge-blue',
  developing: 'badge-yellow',
  needs_support: 'badge-red',
  needs_data: 'badge-orange',
  not_started: 'badge-gray',
  green: 'badge-green', yellow: 'badge-yellow', red: 'badge-red',
};
const FLUENCY_LABELS = {
  fluent: 'Fluent',
  progressing: 'Progressing',
  developing: 'Developing',
  needs_support: 'Needs Support',
  needs_data: 'Needs More Data',
  not_started: 'Not Started',
  green: 'Fluent', yellow: 'Developing', red: 'Needs Support',
};
const TREND_LABELS = { decreasing: 'Decreasing (good)', stable: 'Stable', increasing: 'Increasing' };

export default function StudentDrillDown() {
  const { classroomId, studentId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.studentProgress(studentId, classroomId)
      .then(setData)
      .finally(() => setLoading(false));
  }, [studentId, classroomId]);

  if (loading) return <><Navbar /><p className="text-center text-muted mt-3">Loading...</p></>;
  if (!data) return <><Navbar /><p className="text-center text-muted mt-3">No data found</p></>;

  return (
    <>
      <Navbar />
      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
        <p className="text-sm text-muted" style={{ cursor: 'pointer' }} onClick={() => navigate(`/teacher/classroom/${classroomId}`)}>
          &larr; Back to {data.classroom_name}
        </p>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginTop: '.5rem' }}>{data.student_name}</h1>
        <p className="text-muted text-sm">Detailed progress and growth over time</p>

        {data.skills.length === 0 ? (
          <div className="card text-center mt-3" style={{ padding: '3rem' }}>
            <p style={{ fontWeight: 600 }}>No practice data yet</p>
            <p className="text-muted mt-1">This student hasn't completed any sessions.</p>
          </div>
        ) : (
          data.skills.map((skill, i) => (
            <div key={i} className="card mt-2">
              <div className="flex-between">
                <div>
                  <h3 style={{ fontWeight: 600 }}>{skill.skill_name}</h3>
                  <span className="badge badge-gray">{skill.skill_domain}</span>
                </div>
                <span className={`badge ${FLUENCY_COLORS[skill.fluency_status] || 'badge-gray'}`}>
                  {FLUENCY_LABELS[skill.fluency_status] || skill.fluency_status}
                </span>
              </div>

              {/* Stats Row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'var(--ns-gray-50)', borderRadius: 'var(--ns-radius)' }}>
                <div>
                  <div className="text-sm text-muted">Sessions</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{skill.sessions_completed}</div>
                </div>
                <div>
                  <div className="text-sm text-muted">Accuracy</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{skill.overall_accuracy}%</div>
                </div>
                <div>
                  <div className="text-sm text-muted">Avg Speed</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {skill.avg_response_time_ms ? `${(skill.avg_response_time_ms / 1000).toFixed(1)}s` : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted">Max Level</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {skill.max_difficulty ? `${skill.max_difficulty}/5` : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted">Visual Trend</div>
                  <div style={{ fontSize: '.875rem', fontWeight: 600, color: skill.visual_support_trend === 'decreasing' ? 'var(--ns-green-600)' : 'var(--ns-gray-600)' }}>
                    {TREND_LABELS[skill.visual_support_trend] || skill.visual_support_trend}
                  </div>
                </div>
              </div>

              {/* Growth Table */}
              {skill.growth && skill.growth.length > 0 && (
                <div className="table-wrapper mt-2">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Accuracy</th>
                        <th>Speed</th>
                        <th>Difficulty</th>
                        <th>Visual Level</th>
                      </tr>
                    </thead>
                    <tbody>
                      {skill.growth.map((g, j) => (
                        <tr key={j}>
                          <td className="text-sm">{new Date(g.session_date).toLocaleDateString()}</td>
                          <td>
                            <span className={`badge ${g.accuracy >= 85 ? 'badge-green' : g.accuracy >= 60 ? 'badge-yellow' : 'badge-red'}`}>
                              {g.accuracy}%
                            </span>
                          </td>
                          <td className="text-sm">{(g.avg_time_ms / 1000).toFixed(1)}s</td>
                          <td className="text-sm">{g.difficulty}/5</td>
                          <td className="text-sm">{g.visual_level}/5</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </>
  );
}
