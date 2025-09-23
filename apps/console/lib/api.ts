const API_BASE_ENV = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE;
export const API_BASE = API_BASE_ENV || 'http://127.0.0.1:8001';
const AUTH_DISABLED = (process.env.NEXT_PUBLIC_AUTH_DISABLED || 'false').toLowerCase() === 'true';

function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    const fromStorage = window.localStorage.getItem('api_token');
    if (fromStorage) return fromStorage;
  }
  return process.env.NEXT_PUBLIC_API_TOKEN || null;
}

export function authHeaders(extra?: Record<string, string>): HeadersInit {
  const token = getAuthToken();
  const base: Record<string, string> = extra ? { ...extra } : {};
  if (!AUTH_DISABLED && token) base['Authorization'] = `Bearer ${token}`;
  return base;
}

export async function getJson<T>(path: string): Promise<T> {
  const url = /^https?:\/\//i.test(path) ? path : `${API_BASE}${path}`;
  const res = await fetch(url, { cache: 'no-store', headers: authHeaders() });
  if (!res.ok) throw new Error(`GET ${path} ${res.status}`);
  return res.json();
}

export async function postJson<T>(path: string, body?: any): Promise<T> {
  const url = /^https?:\/\//i.test(path) ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`POST ${path} ${res.status}`);
  return res.json();
}

// Helper: application/x-www-form-urlencoded
export async function postForm<T>(path: string, form: Record<string, string>): Promise<T> {
  const url = /^https?:\/\//i.test(path) ? path : `${API_BASE}${path}`;
  const body = new URLSearchParams(form).toString();
  const res = await fetch(url, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' }),
    body,
  });
  if (!res.ok) throw new Error(`POST ${path} ${res.status}`);
  return res.json();
}

export function saveToken(token: string) {
  try { if (typeof window !== 'undefined') window.localStorage.setItem('api_token', token); } catch {}
}

export function clearToken() {
  try { if (typeof window !== 'undefined') window.localStorage.removeItem('api_token'); } catch {}
}
