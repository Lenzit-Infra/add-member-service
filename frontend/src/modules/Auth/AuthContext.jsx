import React, { createContext, useContext, useEffect, useState } from 'react';
import apiClient, { setAccessToken, setOnAuthFailure } from '../../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setOnAuthFailure(() => setUser(null));

    // Try to silently restore a session using the httpOnly refresh cookie.
    apiClient.post('/account/refresh')
      .then(res => {
        setAccessToken(res.data.access_token);
        setUser(res.data.user);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const login = (accessToken, userInfo) => {
    setAccessToken(accessToken);
    setUser(userInfo);
  };

  const logout = async () => {
    try { await apiClient.post('/account/logout'); } catch (e) { /* ignore */ }
    setAccessToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
