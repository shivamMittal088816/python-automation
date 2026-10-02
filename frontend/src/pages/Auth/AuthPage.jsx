import { useState } from 'react';
import { Link, useLocation } from 'react-router';
import { registerAccount, signIn } from '../../services/auth/api';
import { returnDestination } from './utils/returnDestination';
import { useAuth } from '../../context/AuthContext';
import './auth.css';

export function AuthPage({ register = false }) {
  const location = useLocation();
  const auth = useAuth();
  const [visible, setVisible] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  async function submit(event) {
    event.preventDefault();
    if (pending) return;
    setPending(true); setError('');
    try {
      if (register) await registerAccount({ name, email, password });
      else await signIn({ email, password });
      window.location.assign(returnDestination(location.search));
    } catch (err) { setError(err.message); setPending(false); }
  }
  const next = new URLSearchParams(location.search).get('next');
  const other = `${register ? '/login' : '/register'}${next ? `?next=${encodeURIComponent(next)}` : ''}`;
  return <main className="auth-page">
    <div className="auth-brand"><span className="auth-brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg></span><span>Student Mapping</span></div>
    <div className="auth-layout">
      <aside className="auth-story">
        <span className="auth-eyebrow">A LITTLE LESS ADMIN. A LOT MORE CLARITY.</span>
        <h1>Your student data.<br/><span>Everything in place.</span></h1>
        <p>Map school records, prepare registrations, and bring your team into the same workflow.</p>
        <div className="auth-preview" aria-hidden="true">
          <div className="auth-preview-header"><span className="auth-preview-dot"/> Your workspace <span>Ready to work</span></div>
          <div className="auth-preview-row"><span>01</span><div><strong>Bring your files together</strong><small>School records and student data</small></div><b>✓</b></div>
          <div className="auth-preview-row"><span>02</span><div><strong>Make the right connections</strong><small>Admission numbers, emails, and names</small></div><b>✓</b></div>
          <div className="auth-preview-row"><span>03</span><div><strong>Move forward with confidence</strong><small>Review your results before exporting</small></div><b>↗</b></div>
        </div>
        <p className="auth-story-caption">Less switching between files. More time for what matters.</p>
      </aside>
      <section className="auth-card" aria-labelledby="auth-title">
        <span className="auth-card-eyebrow">{register ? 'GET STARTED' : 'YOUR WORKSPACE AWAITS'}</span>
        <h2 id="auth-title">{register ? 'Create your account' : 'Welcome back'}</h2>
        <p className="auth-card-description">{register ? 'A fresh start for your school workflows.' : 'Sign in to continue where you left off.'}</p>
        {!register && new URLSearchParams(location.search).has('logged_out') && <p className="auth-success" role="status">You’ve been signed out.</p>}
        {auth.user && <p className="auth-success">Signed in as {auth.user.name}. <a href={returnDestination(location.search)}>Continue to workspace</a></p>}
        <form onSubmit={submit}>
          {register && <label htmlFor="auth-name">Full name<input id="auth-name" name="name" value={name} onChange={event => setName(event.target.value)} autoComplete="name" placeholder="Your name" required maxLength={100} disabled={pending}/></label>}
          <label htmlFor="auth-email">Email address<input id="auth-email" name="email" type="email" value={email} onChange={event => setEmail(event.target.value)} autoComplete="email" placeholder="you@school.com" required maxLength={254} disabled={pending}/></label>
          <label htmlFor="auth-password">Password<div className="auth-password-field"><input id="auth-password" name="password" aria-label="Password" type={visible ? 'text' : 'password'} value={password} onChange={event => setPassword(event.target.value)} autoComplete={register ? 'new-password' : 'current-password'} placeholder={register ? 'Choose a strong password' : 'Enter your password'} required minLength={register ? 15 : 1} maxLength={128} disabled={pending} aria-describedby={register ? 'auth-password-help' : undefined}/><button type="button" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} onClick={() => setVisible(value => !value)} disabled={pending}>{visible ? 'Hide' : 'Show'}</button></div></label>
          {register && <p id="auth-password-help" className="auth-help">Use at least 15 characters. A memorable passphrase works well.</p>}
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="auth-submit" type="submit" disabled={pending}>{pending ? register ? 'Creating account…' : 'Signing in…' : register ? 'Create account' : 'Sign in'}<span aria-hidden="true">→</span></button>
        </form>
        <p className="auth-alternative">{register ? 'Already have an account?' : 'New to Student Mapping?'} <Link to={other}>{register ? 'Sign in' : 'Create an account'}</Link></p>
        <div className="auth-card-footer"><svg aria-hidden="true" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="4" y="8" width="12" height="9" rx="2"/><path d="M6 8V6a4 4 0 0 1 8 0v2"/></svg>Your account, securely signed in.</div>
      </section>
    </div>
    <footer className="auth-page-footer">Student Mapping · A clearer way to work with student data.</footer>
  </main>;
}
