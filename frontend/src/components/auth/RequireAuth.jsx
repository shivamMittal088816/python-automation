import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '../../context/AuthContext';

export function RequireAuth() {
  const auth = useAuth();
  const location = useLocation();
  if (auth.loading) return <div className="auth-loading" role="status">Opening your workspace…</div>;
  if (auth.error) return <div className="auth-loading"><p role="alert">{auth.error}</p><button type="button" onClick={auth.retry}>Try again</button></div>;
  if (!auth.user && auth.required) return <Navigate replace to={`/login?next=${encodeURIComponent(location.pathname + location.search + location.hash)}`} />;
  return <Outlet />;
}
