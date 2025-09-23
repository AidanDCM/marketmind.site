import { useEffect, useState } from 'react';

export function parseJwt(token: string): any | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function getRoleFromToken(): string | null {
  try {
    let token: string | null = null;
    if (typeof window !== 'undefined') {
      token = window.localStorage.getItem('api_token');
    }
    if (!token && typeof process !== 'undefined') {
      token = (process.env.NEXT_PUBLIC_API_TOKEN as string) || null;
    }
    if (!token) return null;
    const payload = parseJwt(token);
    return payload?.role || null;
  } catch {
    return null;
  }
}

export function useRole(): { role: string | null, tokenPresent: boolean } {
  const [role, setRole] = useState<string | null>(null);
  const [tokenPresent, setTokenPresent] = useState<boolean>(false);
  useEffect(() => {
    try {
      const tok = typeof window !== 'undefined' ? window.localStorage.getItem('api_token') : null;
      setTokenPresent(!!tok);
      if (tok) {
        const payload = parseJwt(tok);
        setRole(payload?.role || null);
      } else {
        const envTok = (process.env.NEXT_PUBLIC_API_TOKEN as string) || '';
        if (envTok) {
          setTokenPresent(true);
          const payload = parseJwt(envTok);
          setRole(payload?.role || null);
        }
      }
    } catch {
      setRole(null);
    }
  }, []);
  return { role, tokenPresent };
}
