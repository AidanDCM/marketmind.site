"use client";

import React, { useState } from "react";
import { postForm, saveToken, clearToken } from "../../lib/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function doLogin(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      const data = await postForm<{ access_token: string }>("/auth/token", { username, password });
      if (!data?.access_token) throw new Error("No token returned");
      saveToken(data.access_token);
      setMsg("Logged in. Redirecting…");
      setTimeout(() => (window.location.href = "/"), 400);
    } catch (e: any) {
      setMsg(e?.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    clearToken();
    setMsg("Logged out.");
  }

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="bg-white border rounded-xl p-6">
        <h1 className="text-2xl font-semibold mb-2">Login</h1>
        <p className="text-sm text-gray-600 mb-4">Use your username or email and password.</p>
        <form onSubmit={doLogin} className="space-y-3">
          <div className="space-y-1">
            <label className="text-sm text-gray-600">Username or Email</label>
            <input className="border rounded px-3 py-2 w-full" value={username} onChange={(e)=>setUsername(e.target.value)} required />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-gray-600">Password</label>
            <input type="password" className="border rounded px-3 py-2 w-full" value={password} onChange={(e)=>setPassword(e.target.value)} required />
          </div>
          <button className="mm-btn primary w-full" disabled={busy}>{busy ? "Working…" : "Login"}</button>
        </form>
        {msg && <div className="mt-3 text-sm text-gray-700">{msg}</div>}
        <div className="mt-4 text-sm">
          <a href="/onboarding" className="text-blue-600 hover:underline">Go to Onboarding</a>
          <span className="mx-2">·</span>
          <button className="text-gray-600 hover:underline" onClick={logout}>Logout</button>
        </div>
      </div>
    </div>
  );
}
