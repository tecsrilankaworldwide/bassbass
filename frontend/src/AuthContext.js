import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

export const API = process.env.REACT_APP_BACKEND_URL + '/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('bb_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.get(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(res => setUser(res.data.user))
        .catch(() => { localStorage.removeItem('bb_token'); setToken(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem('bb_token', res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const register = async (data) => {
    const res = await axios.post(`${API}/auth/register`, data);
    localStorage.setItem('bb_token', res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('bb_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
