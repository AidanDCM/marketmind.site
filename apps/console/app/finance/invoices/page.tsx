"use client";

import useSWR, { mutate } from "swr";
import { getJson, postJson, API_BASE } from "../../../lib/api";
import React from "react";
import { useRole } from "../../../lib/auth";
import { Modal } from "../../../components/ui/Modal";
import { useToast } from "../../../components/ui/Toast";
import { downloadCsv } from "../../../lib/csv";
import { GuardedButton } from "../../../components/ui/GuardedAction";
import { InlineError } from "../../../components/ui/InlineError";
import { SkeletonText } from "../../../components/ui/Skeleton";
import { Th, Td } from "../../../components/ui/Table";

export default function InvoicesPage(){
  const [status, setStatus] = React.useState<string>("all");
  const [limit, setLimit] = React.useState<number>(50);
  const [offset, setOffset] = React.useState<number>(0);
  const { role, tokenPresent } = useRole();
  const canWrite = !!tokenPresent && ["admin","finance","editor"].includes(role||"");
  const [showNew, setShowNew] = React.useState(false);
  const [form, setForm] = React.useState<any>({ supplier_id: "", invoice_no: "", subtotal: "", tax: "", total: "", invoice_date: "", due_date: "", currency: "USD" });
  const toast = useToast();
  const qs = new URLSearchParams();
  if (status !== "all") qs.set("status_eq", status);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  const { data, error } = useSWR<any>(`${API_BASE}/finance/invoices?${qs.toString()}`, getJson, { refreshInterval: 30000 });
  const items = (data?.items || []) as any[];
  const loading = !data && !error;
  // Error/recovery toasts for consistency
  const hasError = Boolean(error);
  const prevHasError = React.useRef<boolean>(false);
  React.useEffect(() => {
    if (hasError && !prevHasError.current) {
      toast.error('Invoices data unavailable');
    } else if (!hasError && prevHasError.current) {
      toast.success('Invoices data recovered');
    }
    prevHasError.current = hasError;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasError]);

  async function createInvoice(e: React.FormEvent){
    e.preventDefault();
    const payload: any = {
      supplier_id: form.supplier_id ? Number(form.supplier_id) : undefined,
      invoice_no: String(form.invoice_no||"") || undefined,
      subtotal: form.subtotal ? Number(form.subtotal) : 0,
      tax: form.tax ? Number(form.tax) : 0,
      total: form.total ? Number(form.total) : 0,
    };
    if (form.org_id) payload.org_id = form.org_id;
    if (form.invoice_date) payload.invoice_date = form.invoice_date;
    if (form.due_date) payload.due_date = form.due_date;
    if (form.currency) payload.currency = form.currency;
    try {
      await postJson(`/finance/invoices`, payload);
      toast.success('Invoice created');
      setShowNew(false);
      setForm({ supplier_id: "", invoice_no: "", subtotal: "", tax: "", total: "", invoice_date: "", due_date: "", currency: "USD" });
      mutate(`${API_BASE}/finance/invoices?${qs.toString()}`);
    } catch (e:any) {
      toast.error(e?.message || 'Failed to create invoice');
    }
  }

  function exportCsv(){
    const headers = ["id","supplier_id","invoice_no","status","total","invoice_date","due_date"]; 
    const rows = items.map(i=> [i.id, i.supplier_id, i.invoice_no, i.status, i.total, i.invoice_date, i.due_date]);
    downloadCsv("invoices", headers, rows);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Invoices</h1>
        <div className="flex items-center gap-2">
          <select value={status} onChange={e=>setStatus(e.target.value)} className="border rounded px-2 py-1 text-sm">
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="paid">Paid</option>
            <option value="void">Void</option>
            <option value="overdue">Overdue</option>
          </select>
          <input type="number" className="border rounded px-2 py-1 w-24 text-sm" value={limit} onChange={e=>{ const v = Math.max(1, parseInt(e.target.value||'1')); setLimit(v); setOffset(0); }} />
          <div className="flex items-center gap-1">
            <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50 disabled:opacity-50" disabled={offset<=0 || loading} onClick={()=> setOffset(Math.max(0, offset - limit))}>Prev</button>
            <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50 disabled:opacity-50" disabled={loading || items.length < limit} onClick={()=> setOffset(offset + limit)}>Next</button>
            <span className="text-xs text-gray-600 ml-1">Page {Math.floor(offset/limit)+1}</span>
          </div>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={()=>{ toast.success('Refreshing invoices…'); mutate(`${API_BASE}/finance/invoices?${qs.toString()}`); }}>Refresh</button>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={exportCsv}>Export CSV</button>
          <GuardedButton allowed={canWrite} className="px-2 py-1 text-xs rounded-md border bg-blue-600 text-white hover:bg-blue-700" onClick={()=>setShowNew(true)}>
            New Invoice
          </GuardedButton>
        </div>
      </div>

      {error && (
        <InlineError message={String((error as any)?.message || error)} onRetry={()=> mutate(`${API_BASE}/finance/invoices?${qs.toString()}`)} />
      )}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm" aria-label="Invoices table">
          <caption className="sr-only">Invoices with status, totals, and dates</caption>
          <thead>
            <tr className="bg-gray-50 text-left">
              <Th>ID</Th>
              <Th>Supplier</Th>
              <Th>No.</Th>
              <Th>Status</Th>
              <Th>Total</Th>
              <Th>Issued</Th>
              <Th>Due</Th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><Td colSpan={7}><SkeletonText lines={4} /></Td></tr>
            ) : (
              items.map((inv: any) => (
                <tr key={inv.id} className="border-t">
                  <Td>{inv.id}</Td>
                  <Td>{inv.supplier_id}</Td>
                  <Td>{inv.invoice_no}</Td>
                  <Td>{(inv.status||'').toUpperCase()}</Td>
                  <Td>${Number(inv.total||0).toFixed(2)}</Td>
                  <Td>{inv.invoice_date || '—'}</Td>
                  <Td>{inv.due_date || '—'}</Td>
                </tr>
              ))
            )}
            {!loading && !items.length && (
              <tr><Td colSpan={7}><div className="text-gray-500">No invoices.</div></Td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal open={showNew} title="Create Invoice" onClose={()=>setShowNew(false)}>
        {!canWrite ? (
          <div className="text-sm text-red-600">Insufficient role. Login as admin/finance/editor.</div>
        ) : (
          <form onSubmit={createInvoice} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Org ID (optional)"><input className="border rounded px-2 py-1 w-full" value={form.org_id||''} onChange={e=>setForm({...form, org_id:e.target.value})} /></Field>
              <Field label="Supplier ID"><input className="border rounded px-2 py-1 w-full" value={form.supplier_id} onChange={e=>setForm({...form, supplier_id:e.target.value})} required /></Field>
              <Field label="Invoice No."><input className="border rounded px-2 py-1 w-full" value={form.invoice_no} onChange={e=>setForm({...form, invoice_no:e.target.value})} required /></Field>
              <Field label="Currency"><input className="border rounded px-2 py-1 w-full" value={form.currency} onChange={e=>setForm({...form, currency:e.target.value})} /></Field>
              <Field label="Subtotal"><input type="number" step="0.01" className="border rounded px-2 py-1 w-full" value={form.subtotal} onChange={e=>setForm({...form, subtotal:e.target.value})} /></Field>
              <Field label="Tax"><input type="number" step="0.01" className="border rounded px-2 py-1 w-full" value={form.tax} onChange={e=>setForm({...form, tax:e.target.value})} /></Field>
              <Field label="Total"><input type="number" step="0.01" className="border rounded px-2 py-1 w-full" value={form.total} onChange={e=>setForm({...form, total:e.target.value})} /></Field>
              <Field label="Invoice Date (YYYY-MM-DD)"><input className="border rounded px-2 py-1 w-full" value={form.invoice_date} onChange={e=>setForm({...form, invoice_date:e.target.value})} /></Field>
              <Field label="Due Date (YYYY-MM-DD)"><input className="border rounded px-2 py-1 w-full" value={form.due_date} onChange={e=>setForm({...form, due_date:e.target.value})} /></Field>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="px-3 py-1.5 text-sm border rounded" onClick={()=>setShowNew(false)}>Cancel</button>
              <button type="submit" className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white">Create</button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}


function Field({ label, children }:{ label: string; children: React.ReactNode }){
  return (
    <label className="text-sm">
      <div className="text-gray-600 mb-1">{label}</div>
      {children}
    </label>
  );
}
