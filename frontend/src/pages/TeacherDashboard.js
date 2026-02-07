import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import api from '../services/api';

export default function TeacherDashboard() {
  const [classrooms, setClassrooms] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.listClassrooms().then(setClassrooms).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    const c = await api.createClassroom(newName.trim());
    setClassrooms([c, ...classrooms]);
    setNewName('');
    setShowCreate(false);
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
        <div className="flex-between">
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>My Classes</h1>
            <p className="text-sm text-muted mt-1">Manage your classes, assign skills, and track student progress.</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
            + New Class
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="card mt-2" style={{ display: 'flex', gap: '.75rem', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Class Name</label>
              <input className="form-input" value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. 4th Grade Math — Period 1" autoFocus />
            </div>
            <button className="btn btn-primary" type="submit">Create</button>
            <button className="btn btn-secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
          </form>
        )}

        {loading ? (
          <p className="text-center text-muted mt-3">Loading classes...</p>
        ) : classrooms.length === 0 ? (
          <div className="card text-center mt-3" style={{ padding: '3rem' }}>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--ns-gray-700)' }}>No classes yet</p>
            <p className="text-muted mt-1">Create your first class to get started.</p>
          </div>
        ) : (
          <div className="grid-2 mt-2">
            {classrooms.map(c => (
              <div
                key={c.id}
                className="card"
                style={{ cursor: 'pointer', transition: 'box-shadow .15s' }}
                onClick={() => navigate(`/teacher/classroom/${c.id}`)}
                onMouseOver={e => e.currentTarget.style.boxShadow = 'var(--ns-shadow-md)'}
                onMouseOut={e => e.currentTarget.style.boxShadow = 'var(--ns-shadow)'}
              >
                <div className="flex-between">
                  <h3 style={{ fontSize: '1.0625rem', fontWeight: 600 }}>{c.name}</h3>
                  <span className="badge badge-indigo">{c.class_code}</span>
                </div>
                <p className="text-sm text-muted mt-1">
                  {c.student_count} student{c.student_count !== 1 ? 's' : ''}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
