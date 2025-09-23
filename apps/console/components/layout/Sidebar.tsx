"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/onboarding", label: "Onboarding", icon: "🚀" },
  { href: "/", label: "Overview", icon: "📊" },
  { href: "/command-center", label: "Command Center", icon: "🧠" },
  { href: "/pricing", label: "Pricing Lab", icon: "💹" },
  { href: "/finance", label: "Finance", icon: "💼" },
  { href: "/health", label: "Health", icon: "🩺" },
  { href: "/integrations", label: "Integrations", icon: "🔌" },
  { href: "/logs", label: "Logs", icon: "📜" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [brand, setBrand] = useState<string>("MarketMind");
  const [logo, setLogo] = useState<string>("");
  const envName = (process.env.NEXT_PUBLIC_APP_ENV || process.env.NODE_ENV || 'dev').toString();
  useEffect(() => {
    try {
      const b = typeof window !== 'undefined' ? window.localStorage.getItem('mm_brand_name') : '';
      const l = typeof window !== 'undefined' ? window.localStorage.getItem('mm_brand_logo') : '';
      if (b) setBrand(b);
      if (l) setLogo(l);
    } catch {}
  }, []);
  return (
    <aside className="w-60 bg-white border-r border-gray-200 hidden md:flex md:flex-col">
      <div className="h-14 flex items-center gap-2 px-4 border-b">
        {logo ? (
          <img src={logo} alt={brand} className="w-8 h-8 rounded-md object-cover" />
        ) : (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold">🧠</div>
        )}
        <div className="font-semibold truncate" title={brand}>{brand}</div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map((item) => {
          const active = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm ${active ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"}`}>
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-3 text-xs text-gray-500 border-t">v0.1 • {envName}</div>
    </aside>
  );
}
