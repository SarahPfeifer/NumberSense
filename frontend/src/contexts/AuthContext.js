import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('ns_token');
    if (token) {
      api.setToken(token);
      api.getMe()
        .then(u => setUser(u))
        .catch(() => { api.setToken(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password);
    api.setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const classCodeLogin = useCallback(async (code, identifier) => {
    const data = await api.classCodeLogin(code, identifier);
    api.setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (formData) => {
    const data = await api.register(formData);
    api.setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const claimSession = useCallback((token, studentInfo) => {
    api.setToken(token);
    setUser(studentInfo);
  }, []);

  const logout = useCallback(() => {
    api.setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, classCodeLogin, register, claimSession, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
