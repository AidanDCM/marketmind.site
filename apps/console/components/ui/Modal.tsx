"use client";

import React, { useEffect, useRef, useId } from "react";

export function Modal({ open, title, onClose, children }: { open: boolean; title: string; onClose: ()=>void; children: React.ReactNode }){
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent){
      if (e.key === 'Escape') { onClose(); return; }
      if (e.key === 'Tab') {
        const root = dialogRef.current;
        if (!root) return;
        const focusables = root.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length-1];
        const active = document.activeElement as HTMLElement | null;
        if (e.shiftKey) {
          if (active === first || !root.contains(active)) { e.preventDefault(); last.focus(); }
        } else {
          if (active === last || !root.contains(active)) { e.preventDefault(); first.focus(); }
        }
      }
    }
    window.addEventListener('keydown', onKey);
    // Initial focus
    const t = setTimeout(() => {
      const root = dialogRef.current;
      if (!root) return;
      const first = root.querySelector<HTMLElement>('input, select, textarea, button');
      (first || root).focus();
    }, 0);
    return () => { window.removeEventListener('keydown', onKey); clearTimeout(t); };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div ref={dialogRef} className="relative bg-white rounded-xl border shadow-lg w-full max-w-lg outline outline-2 outline-transparent focus-within:outline-blue-500">
        <div className="p-4 border-b flex items-center justify-between">
          <div id={titleId} className="font-semibold">{title}</div>
          <button className="text-gray-500 hover:text-gray-700" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
}
