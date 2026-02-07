import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const goHome = () => {
    navigate(user?.role === 'teacher' ? '/teacher' : '/student');
  };

  return (
    <nav className="topnav">
      <span className="topnav-brand" style={{ cursor: 'pointer' }} onClick={goHome}>
        NumberSense
      </span>
      <div className="topnav-actions">
        {user && (
          <>
            <span className="text-sm text-muted">
              {user.first_name} {user.last_name}
              <span className="badge badge-indigo" style={{ marginLeft: 8 }}>
                {user.role}
              </span>
            </span>
            <button className="btn btn-secondary" onClick={handleLogout} style={{ padding: '.375rem .75rem', fontSize: '.8125rem' }}>
              Log out
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
