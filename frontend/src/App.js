import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TeacherDashboard from './pages/TeacherDashboard';
import ClassroomDetail from './pages/ClassroomDetail';
import AssignSkill from './pages/AssignSkill';
import StudentDrillDown from './pages/StudentDrillDown';
import StudentHome from './pages/StudentHome';
import PracticeSession from './pages/PracticeSession';
import SessionComplete from './pages/SessionComplete';
import GoogleCallback from './pages/GoogleCallback';
import SharedAssignment from './pages/SharedAssignment';

function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="text-center mt-3">Loading...</div>;
  if (!user) {
    // Preserve the current path so we can redirect back after login
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?redirect=${redirect}`} />;
  }
  if (role && user.role !== role) return <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} />;
  return children;
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p style={{ color: '#6B7280' }}>Loading NumberSense...</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to="/teacher" /> : <RegisterPage />} />

      {/* Teacher routes */}
      <Route path="/teacher" element={<ProtectedRoute role="teacher"><TeacherDashboard /></ProtectedRoute>} />
      <Route path="/teacher/classroom/:id" element={<ProtectedRoute role="teacher"><ClassroomDetail /></ProtectedRoute>} />
      <Route path="/teacher/classroom/:id/assign" element={<ProtectedRoute role="teacher"><AssignSkill /></ProtectedRoute>} />
      <Route path="/teacher/classroom/:classroomId/student/:studentId" element={<ProtectedRoute role="teacher"><StudentDrillDown /></ProtectedRoute>} />
      <Route path="/teacher/google/callback" element={<ProtectedRoute role="teacher"><GoogleCallback /></ProtectedRoute>} />

      {/* Student routes */}
      <Route path="/student" element={<ProtectedRoute role="student"><StudentHome /></ProtectedRoute>} />
      <Route path="/student/practice/:assignmentId" element={<ProtectedRoute role="student"><PracticeSession /></ProtectedRoute>} />
      <Route path="/student/complete/:sessionId" element={<ProtectedRoute role="student"><SessionComplete /></ProtectedRoute>} />

      {/* Shared assignment — no login required */}
      <Route path="/go/:shareToken" element={<SharedAssignment />} />

      {/* Default */}
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}
