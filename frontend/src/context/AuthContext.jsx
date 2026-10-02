import { createContext, useContext, useEffect, useState } from 'react';
import { getCurrentAccount } from '../services/auth/api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [state, setState] = useState({ user: null, required: true, loading: true, error: '' });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const expired = () => setState(value => value.required ? { ...value, user: null, loading: false } : value);
    window.addEventListener('auth-expired', expired);
    return () => window.removeEventListener('auth-expired', expired);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    getCurrentAccount(controller.signal).then(result => {
      if (!controller.signal.aborted) setState({ ...result, loading: false, error: '' });
    }).catch(error => {
      if (!controller.signal.aborted) setState({ user: null, required: true, loading: false, error: error.message });
    });
    return () => controller.abort();
  }, [retry]);
  return <AuthContext.Provider value={{ ...state, retry: () => { setState(value => ({ ...value, loading: true })); setRetry(value => value + 1); } }}>{children}</AuthContext.Provider>;
}
