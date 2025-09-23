"use client";

import React, { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { API_BASE } from "../../lib/api";

const PUBLIC_ROUTES = new Set(["/login", "/privacy", "/terms"]);
const ONBOARDING_PUBLIC = (process.env.NEXT_PUBLIC_ONBOARDING_PUBLIC || "true").toLowerCase() === "true";
const AUTH_DISABLED = (process.env.NEXT_PUBLIC_AUTH_DISABLED || "false").toLowerCase() === "true";

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (AUTH_DISABLED) {
        // Local single-team mode: allow everything without token checks
        if (!cancelled) {
          setAllowed(true);
          setChecking(false);
        }
        return;
      }
      const path = pathname || "/";
      const publicRoute = PUBLIC_ROUTES.has(path) || (ONBOARDING_PUBLIC && path.startsWith("/onboarding"));

      // Token from localStorage (client-only)
      let token: string | null = null;
      try {
        token = typeof window !== "undefined" ? window.localStorage.getItem("api_token") : null;
      } catch {}

      if (!token) {
        if (!publicRoute) {
          if (!cancelled) setAllowed(false);
          if (!cancelled) setChecking(false);
          router.replace("/login");
          return;
        }
        if (!cancelled) {
          setAllowed(true);
          setChecking(false);
        }
        return;
      }

      // Lightweight token verification (optional): fetch /auth/users/me
      try {
        const res = await fetch(`${API_BASE}/auth/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (res.ok) {
          if (!cancelled) setAllowed(true);
        } else {
          // Invalid token, clear and redirect
          try { if (typeof window !== "undefined") window.localStorage.removeItem("api_token"); } catch {}
          if (!publicRoute) router.replace("/login");
          if (!cancelled) setAllowed(publicRoute);
        }
      } catch {
        // Network error - allow rendering, individual panels will handle errors
        if (!cancelled) setAllowed(true);
      } finally {
        if (!cancelled) setChecking(false);
      }
    }
    run();
    return () => { cancelled = true; };
  }, [pathname, router]);

  if (checking) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <div className="mm-card p-4 text-sm text-gray-600">Checking session…</div>
      </div>
    );
  }

  if (!allowed) return null;
  return <>{children}</>;
}
