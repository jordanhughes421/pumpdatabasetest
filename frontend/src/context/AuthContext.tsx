import React, { createContext, useContext, useState, useEffect } from 'react';
import { getMe } from '../api/client';

interface User {
  email: string;
  is_active: boolean;
}

interface Organization {
  id: number;
  name: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  activeOrg: Organization | null;
  role: string | null;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (token: string, user: User, activeOrg: Organization, role: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    token: localStorage.getItem('token'),
    user: null,
    activeOrg: null,
    role: null,
    isLoading: true,
  });

  useEffect(() => {
    // Initial load: verify token or just decode if we trust localStorage (MVP)
    // Better: call /auth/me
    const initAuth = async () => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                // Use client which handles interceptors
                const data = await getMe();
                setState({
                    token: token,
                    user: data.user,
                    activeOrg: data.active_org,
                    role: data.role,
                    isLoading: false
                });
                return;
            } catch (e) {
                console.error("Auth check failed", e);
                localStorage.removeItem('token');
            }
        }
        setState(s => ({ ...s, token: null, isLoading: false }));
    };
    initAuth();
  }, []);

  const login = (token: string, user: User, activeOrg: Organization, role: string) => {
    localStorage.setItem('token', token);
    setState({ token, user, activeOrg, role, isLoading: false });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setState({ token: null, user: null, activeOrg: null, role: null, isLoading: false });
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {!state.isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
