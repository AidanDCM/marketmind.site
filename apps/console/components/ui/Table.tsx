"use client";

import React from "react";

type ThProps = React.ThHTMLAttributes<HTMLTableCellElement> & { children: React.ReactNode; className?: string };
export function Th({ children, className, ...rest }: ThProps){
  return <th scope="col" className={`p-2 border-b ${className||''}`} {...rest}>{children}</th>;
}

type TdProps = React.TdHTMLAttributes<HTMLTableCellElement> & { children: React.ReactNode; className?: string };
export function Td({ children, className, ...rest }: TdProps){
  return <td className={`p-2 ${className||''}`} {...rest}>{children}</td>;
}
