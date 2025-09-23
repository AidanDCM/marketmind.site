"use client";

import React from "react";

export function GuardedButton({
  allowed,
  children,
  onClick,
  className,
  titleWhenDenied = "Insufficient permissions (requires admin/finance/editor)",
  type = "button",
}: {
  allowed: boolean;
  children: React.ReactNode;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  className?: string;
  titleWhenDenied?: string;
  type?: "button" | "submit" | "reset";
}){
  if (allowed) {
    return (
      <button type={type} className={className} onClick={onClick}>
        {children}
      </button>
    );
  }
  return (
    <button type={type} className={`${className} opacity-60 cursor-not-allowed`} onClick={(e)=>e.preventDefault()} aria-disabled title={titleWhenDenied}>
      {children}
    </button>
  );
}
