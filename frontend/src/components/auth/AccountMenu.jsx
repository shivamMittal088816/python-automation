import { useState } from 'react';
import { Link } from 'react-router';
import { useAuth } from '../../context/AuthContext';
import { signOut } from '../../services/auth/api';
import '../../pages/Auth/auth.css';

export function AccountMenu() {
  const auth = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  if (!auth?.user) return <Link className="account-signin" to="/login">Sign in</Link>;
  async function logout() {
    setPending(true); setError('');
    try { await signOut(); window.location.assign('/login?logged_out=1'); }
    catch (err) { setError(err.message); setPending(false); }
  }
  return <details className="account-menu"><summary aria-label="Account menu"><span className="account-avatar">{auth.user.name.slice(0, 1).toUpperCase()}</span><span className="account-name">{auth.user.name}</span><span aria-hidden="true">⌄</span></summary><div className="account-panel"><strong>{auth.user.name}</strong><p>{auth.user.email}</p>{error && <p role="alert">{error}</p>}<button type="button" disabled={pending} onClick={logout}>{pending ? 'Signing out…' : 'Sign out'}<span aria-hidden="true">↗</span></button></div></details>;
}
