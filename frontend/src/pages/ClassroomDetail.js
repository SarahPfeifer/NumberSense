import React, { useState, useEffect, useCallback } from 'react';
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
  // Legacy fallback
  green: 'badge-green', yellow: 'badge-yellow', red: 'badge-red',
};
const FLUENCY_LABELS = {
  fluent: 'Fluent',
  progressing: 'Progressing',
  developing: 'Developing',
  needs_support: 'Needs Support',
  needs_data: 'Needs More Data',
  not_started: 'Not Started',
  // Legacy fallback
  green: 'Fluent', yellow: 'Developing', red: 'Needs Support',
};

export default function ClassroomDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [classroom, setClassroom] = useState(null);
  const [students, setStudents] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [overview, setOverview] = useState(null);
  const [tab, setTab] = useState('overview');
  const [showEnroll, setShowEnroll] = useState(false);
  const [enrollForm, setEnrollForm] = useState({ first_name: '', last_name: '' });
  const [loading, setLoading] = useState(true);

  // Google Classroom state
  const [googleConnected, setGoogleConnected] = useState(false);
  const [gcPostModal, setGcPostModal] = useState(null);   // assignment being posted
  const [gcCourses, setGcCourses] = useState([]);
  const [gcSelectedCourse, setGcSelectedCourse] = useState('');
  const [gcDueDate, setGcDueDate] = useState('');
  const [gcPosting, setGcPosting] = useState(false);
  const [gcLinks, setGcLinks] = useState({});              // assignment_id → [links]

  const loadData = useCallback(async () => {
    try {
      const [c, s, a, o, gs] = await Promise.all([
        api.getClassroom(id),
        api.listStudents(id),
        api.listAssignments(id),
        api.classroomOverview(id).catch(() => null),
        api.googleStatus().catch(() => ({ connected: false })),
      ]);
      setClassroom(c);
      setStudents(s);
      setAssignments(a);
      setOverview(o);
      setGoogleConnected(gs.connected);

      // Load Google Classroom links for each assignment
      if (gs.connected && a.length > 0) {
        const linkResults = {};
        await Promise.all(a.map(async (asgn) => {
          try {
            const res = await api.googleAssignmentLinks(asgn.id);
            if (res.links && res.links.length > 0) linkResults[asgn.id] = res.links;
          } catch {}
        }));
        setGcLinks(linkResults);
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleEnroll = async (e) => {
    e.preventDefault();
    await api.enrollStudent(id, enrollForm);
    setEnrollForm({ first_name: '', last_name: '' });
    setShowEnroll(false);
    loadData();
  };

  const handleDeleteAssignment = async (aid) => {
    if (!window.confirm('Remove this assignment?')) return;
    await api.deleteAssignment(aid);
    loadData();
  };

  const openPostToClassroom = async (assignment) => {
    setGcPostModal(assignment);
    setGcSelectedCourse('');
    setGcDueDate('');
    setGcPosting(false);
    try {
      const res = await api.googleListCourses();
      setGcCourses(res.courses || []);
    } catch {
      setGcCourses([]);
    }
  };

  const handlePostToClassroom = async () => {
    if (!gcSelectedCourse || !gcPostModal) return;
    setGcPosting(true);
    try {
      await api.googlePostAssignment({
        assignment_id: gcPostModal.id,
        course_id: gcSelectedCourse,
        due_date: gcDueDate || null,
      });
      setGcPostModal(null);
      loadData();
    } catch (err) {
      alert(err.message || 'Failed to post to Google Classroom.');
    } finally {
      setGcPosting(false);
    }
  };

  if (loading) return <><Navbar /><p className="text-center text-muted mt-3">Loading...</p></>;
  if (!classroom) return <><Navbar /><p className="text-center text-muted mt-3">Classroom not found</p></>;

  return (
    <>
      <Navbar />
      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
        <div className="flex-between">
          <div>
            <p className="text-sm text-muted" style={{ cursor: 'pointer' }} onClick={() => navigate('/teacher')}>
              &larr; All Classes
            </p>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginTop: '.25rem' }}>{classroom.name}</h1>
            <div className="flex gap-1 mt-1">
              <span className="badge badge-indigo">Code: {classroom.class_code}</span>
              <span className="badge badge-gray">{students.length} students</span>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate(`/teacher/classroom/${id}/assign`)}>
            Assign Skill
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '2px solid var(--ns-gray-200)', marginTop: '1.5rem' }}>
          {['overview', 'students', 'assignments'].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: '.75rem 1.25rem', border: 'none', background: 'none',
              fontWeight: 600, fontSize: '.875rem', cursor: 'pointer', fontFamily: 'var(--ns-font)',
              borderBottom: tab === t ? '2px solid var(--ns-indigo-600)' : '2px solid transparent',
              color: tab === t ? 'var(--ns-indigo-600)' : 'var(--ns-gray-500)',
              marginBottom: -2, textTransform: 'capitalize',
            }}>
              {t}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div style={{ marginTop: '1.5rem' }}>
          {tab === 'overview' && (
            overview && overview.skills && overview.skills.length > 0 ? (
              overview.skills.map(skill => (
                <div key={skill.skill_id} className="card mb-2">
                  <div className="flex-between mb-2">
                    <div>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{skill.skill_name}</h3>
                      <span className="badge badge-gray">{skill.skill_domain}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--ns-indigo-600)' }}>
                        {skill.class_accuracy}%
                      </div>
                      <span className="text-sm text-muted">class accuracy</span>
                    </div>
                  </div>
                  <div className="text-sm text-muted mb-2">Completed: {skill.completion_rate}</div>
                  {/* Skill heat map */}
                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>Student</th>
                          <th>Accuracy</th>
                          <th>Avg Time</th>
                          <th>Sessions</th>
                          <th>Level</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {skill.students.map(s => (
                          <tr key={s.student_id} style={{ cursor: 'pointer' }}
                              onClick={() => navigate(`/teacher/classroom/${id}/student/${s.student_id}`)}>
                            <td style={{ fontWeight: 500 }}>{s.student_name}</td>
                            <td>{s.accuracy !== null ? `${s.accuracy}%` : '—'}</td>
                            <td>{s.avg_time_ms ? `${(s.avg_time_ms / 1000).toFixed(1)}s` : '—'}</td>
                            <td>{s.sessions_completed}</td>
                            <td>{s.max_difficulty ? `${s.max_difficulty}/5` : '—'}</td>
                            <td>
                              <span className={`badge ${FLUENCY_COLORS[s.fluency_status] || 'badge-gray'}`}>
                                {FLUENCY_LABELS[s.fluency_status] || s.fluency_status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            ) : (
              <div className="card text-center" style={{ padding: '3rem' }}>
                <p style={{ fontWeight: 600, color: 'var(--ns-gray-700)' }}>No data yet</p>
                <p className="text-muted mt-1">Assign a skill to start tracking progress.</p>
              </div>
            )
          )}

          {tab === 'students' && (
            <>
              <div className="flex-between mb-2">
                <h3 style={{ fontWeight: 600 }}>Students ({students.length})</h3>
                <button className="btn btn-secondary" onClick={() => setShowEnroll(!showEnroll)}>+ Add Student</button>
              </div>
              {showEnroll && (
                <form onSubmit={handleEnroll} className="card mb-2" style={{ display: 'flex', gap: '.75rem', alignItems: 'flex-end' }}>
                  <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                    <label>First Name</label>
                    <input className="form-input" value={enrollForm.first_name} onChange={e => setEnrollForm({...enrollForm, first_name: e.target.value})} required />
                  </div>
                  <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                    <label>Last Name</label>
                    <input className="form-input" value={enrollForm.last_name} onChange={e => setEnrollForm({...enrollForm, last_name: e.target.value})} required />
                  </div>
                  <button className="btn btn-primary" type="submit">Add</button>
                </form>
              )}
              <div className="card">
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr><th>Name</th><th>Enrolled</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                      {students.map(s => (
                        <tr key={s.id}>
                          <td style={{ fontWeight: 500 }}>{s.student_name}</td>
                          <td className="text-sm text-muted">{new Date(s.enrolled_at).toLocaleDateString()}</td>
                          <td>
                            <button className="btn btn-secondary" style={{ padding: '.25rem .5rem', fontSize: '.75rem' }}
                              onClick={() => navigate(`/teacher/classroom/${id}/student/${s.student_id}`)}>
                              View Progress
                            </button>
                          </td>
                        </tr>
                      ))}
                      {students.length === 0 && (
                        <tr><td colSpan={3} className="text-center text-muted">No students enrolled</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {tab === 'assignments' && (
            <>
              <div className="flex-between mb-2">
                <h3 style={{ fontWeight: 600 }}>Active Assignments</h3>
                <button className="btn btn-primary" onClick={() => navigate(`/teacher/classroom/${id}/assign`)}>+ Assign Skill</button>
              </div>
              {assignments.length === 0 ? (
                <div className="card text-center" style={{ padding: '3rem' }}>
                  <p style={{ fontWeight: 600, color: 'var(--ns-gray-700)' }}>No assignments yet</p>
                  <p className="text-muted mt-1">Click "Assign Skill" to create your first assignment.</p>
                </div>
              ) : (
                <div className="grid-2">
                  {assignments.map(a => {
                    const links = gcLinks[a.id] || [];
                    return (
                      <div key={a.id} className="card">
                        <div className="flex-between">
                          <div>
                            <h4 style={{ fontWeight: 600, fontSize: '.9375rem' }}>{a.skill_name}</h4>
                            <span className="badge badge-gray mt-1">{a.skill_domain}</span>
                          </div>
                          <button className="btn btn-secondary" style={{ padding: '.25rem .5rem', fontSize: '.75rem', color: 'var(--ns-red-500)' }}
                            onClick={() => handleDeleteAssignment(a.id)}>
                            Remove
                          </button>
                        </div>
                        <div className="flex gap-1 mt-2 text-sm text-muted" style={{ flexWrap: 'wrap' }}>
                          <span>Completed: {a.completion_count}/{a.total_students}</span>
                          {a.visual_supports && <span className="badge badge-indigo">Visuals ON</span>}
                          {a.time_limit_seconds && <span className="badge badge-yellow">{a.time_limit_seconds/60}m limit</span>}
                        </div>

                        {/* Google Classroom status */}
                        {links.length > 0 ? (
                          <div style={{ marginTop: '.75rem', padding: '.5rem .75rem', background: '#E8F5E9', borderRadius: 'var(--ns-radius)', fontSize: '.8125rem', color: '#2E7D32' }}>
                            Posted to: {links.map(l => l.course_name || 'Classroom').join(', ')}
                          </div>
                        ) : googleConnected ? (
                          <button className="btn btn-secondary mt-2"
                            style={{ fontSize: '.8125rem', width: '100%' }}
                            onClick={() => openPostToClassroom(a)}>
                            Post to Google Classroom
                          </button>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Post to Google Classroom Modal */}
      {gcPostModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setGcPostModal(null)}>
          <div className="card" style={{ maxWidth: 440, width: '100%', margin: '1rem', padding: '2rem' }}
            onClick={e => e.stopPropagation()}>
            <h3 style={{ fontWeight: 700, fontSize: '1.125rem', marginBottom: '.25rem' }}>
              Post to Google Classroom
            </h3>
            <p className="text-sm text-muted" style={{ marginBottom: '1.25rem' }}>
              Post "{gcPostModal.skill_name}" so students can find it in Classroom.
            </p>

            <div className="form-group">
              <label>Select a Classroom course</label>
              {gcCourses.length === 0 ? (
                <p className="text-sm text-muted">Loading courses...</p>
              ) : (
                <select className="form-input" value={gcSelectedCourse}
                  onChange={e => setGcSelectedCourse(e.target.value)}>
                  <option value="">Choose a course...</option>
                  {gcCourses.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.name}{c.section ? ` — ${c.section}` : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="form-group">
              <label>Due date (optional)</label>
              <input className="form-input" type="date" value={gcDueDate}
                onChange={e => setGcDueDate(e.target.value)} />
            </div>

            <div style={{ display: 'flex', gap: '.75rem', marginTop: '1rem' }}>
              <button className="btn btn-primary" style={{ flex: 1 }}
                onClick={handlePostToClassroom}
                disabled={!gcSelectedCourse || gcPosting}>
                {gcPosting ? 'Posting...' : 'Post Assignment'}
              </button>
              <button className="btn btn-secondary" onClick={() => setGcPostModal(null)}
                disabled={gcPosting}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
