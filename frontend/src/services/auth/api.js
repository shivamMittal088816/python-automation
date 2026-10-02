import { request } from '../api';

export function getCurrentAccount(signal) {
  return request('/auth/me', { signal });
}

export function registerAccount({ name, email, password }) {
  return request('/auth/register', { method: 'POST', body: { name, email, password } });
}

export function signIn({ email, password }) {
  return request('/auth/login', { method: 'POST', body: { email, password } });
}

export function signOut() {
  return request('/auth/logout', { method: 'POST' });
}
