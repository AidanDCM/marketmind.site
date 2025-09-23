"use client";
import React, { createContext, useCallback, useContext, useMemo, useState } from "react";

type ToastType = "success" | "error" | "info";

type ToastItem = { id: number; msg: string; type?: ToastType };

type ToastApi = {
  push: (msg: string, type?: ToastType) => void;
  success: (msg: string) => void;
  error: (msg: string) => void;
  info: (msg: string) => void;
};

const ToastCtx = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const push = useCallback((msg: string, type?: ToastType) => {
    const id = Math.floor(Date.now() + Math.random() * 1000);
    setToasts((prev) => [...prev, { id, msg, type }]);
    if (typeof window !== "undefined") {
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3500);
    }
  }, []);

  const api = useMemo<ToastApi>(() => ({
    push,
    success: (m) => push(m, "success"),
    error: (m) => push(m, "error"),
    info: (m) => push(m, "info"),
  }), [push]);

  return (
    <ToastCtx.Provider value={api}>
      {children}
      <Toaster items={toasts} />
    </ToastCtx.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastCtx);
  if (!ctx) return { push: () => {}, success: () => {}, error: () => {}, info: () => {} };
  return ctx;
}

function Toaster({ items }: { items: ToastItem[] }) {
  const color = (t?: ToastType) => t === "success" ? "bg-emerald-600" : t === "error" ? "bg-red-600" : "bg-gray-800";
  return (
    <div style={{ position: "fixed", top: 16, right: 16, zIndex: 1000 }} aria-live="polite" aria-atomic="true">
      <div className="flex flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={`text-white text-sm px-3 py-2 rounded shadow ${color(t.type)}`}
            role={t.type === "error" ? "alert" : "status"}
          >
            {t.msg}
          </div>
        ))}
      </div>
    </div>
  );
}
