import { createContext, FormEvent, ReactNode, useContext, useEffect, useState, useCallback } from 'react';
import {
  User,
  authAPI,
  tokenStore,
  getApiError,
} from '../services/api';

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (payload: {
    username: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    email: string;
    club_name: string;
  }) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (!tokenStore.getAccess()) {
        setLoading(false);
        return;
      }
      try {
        setUser(await authAPI.me());
      } catch {
        tokenStore.clear();
      } finally {
        setLoading(false);
      }
    };
    load();
    const handleLogout = () => setUser(null);
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setUser(await authAPI.login(username, password));
  }, []);

  const register = useCallback(async (payload: {
    username: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    email: string;
    club_name: string;
  }) => {
    setUser(await authAPI.register(payload));
  }, []);

  const logout = useCallback(() => {
    authAPI.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('Auth konteksti topilmadi');
  return value;
}