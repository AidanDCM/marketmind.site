"use client";

import useSWR, { mutate } from "swr";
import { getJson, postJson, API_BASE } from "../../../lib/api";
import React from "react";
import Link from "next/link";
import { useRole } from "../../../lib/auth";
import { Modal } from "../../../components/ui/Modal";
import { useToast } from "../../../components/ui/Toast";
import { downloadCsv } from "../../../lib/csv";
import { GuardedButton } from "../../../components/ui/GuardedAction";
import { InlineError } from "../../../components/ui/InlineError";
import { SkeletonText } from "../../../components/ui/Skeleton";
import { Th, Td } from "../../../components/ui/Table";

export default function LedgerPage(){
  const [org, setOrg] = React.useState<string>("");
  const [batchId, setBatchId] = React.useState<string>("");
  const [limitB, setLimitB] = React.useState<number>(50);
  const [offsetB, setOffsetB] = React.useState<number>(0);
  const [limitE, setLimitE] = React.useState<number>(50);
  const [offsetE, setOffsetE] = React.useState<number>(0);
  const { role, tokenPresent } = useRole();
  const canWrite = !!tokenPresent && ["admin","finance","editor"].includes(role||"");
  const [showNewBatch, setShowNewBatch] = React.useState(false);
  const [showNewEntry, setShowNewEntry] = React.useState(false);
  const [formBatch, setFormBatch] = React.useState<any>({ org_id: "", source: "manual", posted: false });
  const [formEntry, setFormEntry] = React.useState<any>({ entry_batch_id: "", account_id: "", amount: "", debit: true, ref_type: "", ref_id: "" });
  const [reconBusy, setReconBusy] = React.useState(false);
  const [reconMsg, setReconMsg] = React.useState<string>("");
  const [lastReconId, setLastReconId] = React.useState<string>("");
  const toast = useToast();

  const qsBatches = new URLSearchParams();
  if (org) qsBatches.set("org_id", org);
  qsBatches.set("limit", String(limitB));
  qsBatches.set("offset", String(offsetB));
  const { data: batches, error: batchesError } = useSWR<any>(`${API_BASE}/finance/ledger/batches?${qsBatches.toString()}`, getJson, { refreshInterval: 30000 });

  const qsEntries = new URLSearchParams();
  if (org) qsEntries.set("org_id", org);
  if (batchId) qsEntries.set("entry_batch_id", batchId);
  qsEntries.set("limit", String(limitE));
  qsEntries.set("offset", String(offsetE));
  const { data: entries, error: entriesError } = useSWR<any>(`${API_BASE}/finance/ledger/entries?${qsEntries.toString()}`, getJson, { refreshInterval: 30000 });

  const batchesLoading = !batches && !batchesError;
  const entriesLoading = !entries && !entriesError;

  // Error/recovery toasts for consistency
  const hasError = Boolean(batchesError || entriesError);
  const prevHasErrorRef = React.useRef<boolean>(false);
  React.useEffect(() => {
    if (hasError && !prevHasErrorRef.current) {
      toast.error('Ledger data unavailable');
    } else if (!hasError && prevHasErrorRef.current) {
      toast.success('Ledger data recovered');
    }
    prevHasErrorRef.current = hasError;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasError]);

  function exportBatchesCsv(){
    const items = (batches?.items||[]) as any[];
    const headers = ["id","org_id","ts","source","posted"];
    const rows = items.map(b => [b.id, b.org_id, b.ts, b.source, b.posted]);
    downloadCsv("ledger_batches", headers, rows);
  }

  function exportEntriesCsv(){
    const items = (entries?.items||[]) as any[];
    const headers = ["id","entry_batch_id","account_id","amount","debit","ref_type","ref_id"];
    const rows = items.map(e => [e.id, e.entry_batch_id, e.account_id, e.amount, e.debit, e.ref_type, e.ref_id]);
    downloadCsv("ledger_entries", headers, rows);
  }

  async function createBatch(e: React.FormEvent){
    e.preventDefault();
    try{
      const payload: any = { source: formBatch.source || "manual", posted: !!formBatch.posted };
      if (formBatch.org_id) payload.org_id = formBatch.org_id;
      await postJson(`/finance/ledger/batches`, payload);
      toast.success('Ledger batch created');
      setShowNewBatch(false); setFormBatch({ org_id: "", source: "manual", posted: false });
      mutate(`${API_BASE}/finance/ledger/batches?${qsBatches.toString()}`);
    } catch(err:any){
      toast.error(err?.message || 'Failed to create batch');
    }
  }

  async function createEntry(e: React.FormEvent){
    e.preventDefault();
    try{
      const payload: any = {
        entry_batch_id: formEntry.entry_batch_id ? Number(formEntry.entry_batch_id) : undefined,
        account_id: formEntry.account_id ? Number(formEntry.account_id) : undefined,
        amount: formEntry.amount ? Number(formEntry.amount) : 0,
        debit: !!formEntry.debit,
      };
      if (formEntry.ref_type) payload.ref_type = formEntry.ref_type;
      if (formEntry.ref_id) payload.ref_id = formEntry.ref_id;
      await postJson(`/finance/ledger/entries`, payload);
      toast.success('Ledger entry created');
      setShowNewEntry(false); setFormEntry({ entry_batch_id: "", account_id: "", amount: "", debit: true, ref_type: "", ref_id: "" });
      mutate(`${API_BASE}/finance/ledger/entries?${qsEntries.toString()}`);
    } catch(err:any){
      toast.error(err?.message || 'Failed to create entry');
    }
  }

  async function runReconciliation(){
    try{
      setReconBusy(true); setReconMsg("");
      const payload: any = {}; if (org) payload.org_id = org;
      const res = await postJson<{ id: string }>(`/finance/recon/tasks`, payload);
      const message = `Recon task started: ${res?.id || 'ok'}`;
      setReconMsg(message);
      if (res?.id) setLastReconId(res.id);
      toast.success(message);
    } catch(err:any){
      const message = `Recon failed: ${err?.message||err}`;
      setReconMsg(message);
      toast.error(message);
    } finally { setReconBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Ledger</h1>
        <div className="flex items-center gap-2">
          <input placeholder="org_id" className="border rounded px-2 py-1 text-sm" value={org} onChange={e=>setOrg(e.target.value)} />
          <input placeholder="batch id" className="border rounded px-2 py-1 text-sm" value={batchId} onChange={e=>setBatchId(e.target.value)} />
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={()=>{ toast.success('Refreshing ledger…'); mutate(`${API_BASE}/finance/ledger/batches?${qsBatches.toString()}`); mutate(`${API_BASE}/finance/ledger/entries?${qsEntries.toString()}`); }}>Refresh</button>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={exportBatchesCsv}>Export Batches</button>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={exportEntriesCsv}>Export Entries</button>
          <GuardedButton allowed={canWrite} className="px-2 py-1 text-xs rounded-md border bg-blue-600 text-white hover:bg-blue-700" onClick={()=>setShowNewBatch(true)}>
            New Batch
          </GuardedButton>
          <GuardedButton allowed={canWrite} className="px-2 py-1 text-xs rounded-md border bg-blue-600 text-white hover:bg-blue-700" onClick={()=>setShowNewEntry(true)}>
            New Entry
          </GuardedButton>
          <GuardedButton allowed={canWrite} className="px-2 py-1 text-xs rounded-md border bg-emerald-600 text-white hover:bg-emerald-700" onClick={runReconciliation}>
            {reconBusy? 'Recon…':'Run Recon'}
          </GuardedButton>
        </div>
      </div>
      {reconMsg && <div className="text-xs text-gray-600">{reconMsg}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="bg-white rounded-xl border overflow-hidden">
          <div className="p-3 border-b flex items-center justify-between">
            <h2 className="font-semibold">Batches</h2>
            <div className="flex items-center gap-2 text-xs">
              <label className="flex items-center gap-1">Limit <input className="border rounded px-1 py-0.5 w-16" type="number" value={limitB} onChange={e=>{ const v=Math.max(1, parseInt(e.target.value||'1')); setLimitB(v); setOffsetB(0); }}/></label>
              <button className="px-2 py-1 rounded border bg-white hover:bg-gray-50 disabled:opacity-50" disabled={offsetB<=0 || batchesLoading} onClick={()=> setOffsetB(Math.max(0, offsetB - limitB))}>Prev</button>
              <button className="px-2 py-1 rounded border bg-white hover:bg-gray-50 disabled:opacity-50" disabled={batchesLoading || (batches?.items||[]).length < limitB} onClick={()=> setOffsetB(offsetB + limitB)}>Next</button>
              <span>Page {Math.floor(offsetB/limitB)+1}</span>
            </div>
          </div>
          {batchesError && (
            <div className="p-3"><InlineError message={String((batchesError as any)?.message || batchesError)} onRetry={()=> mutate(`${API_BASE}/finance/ledger/batches?${qsBatches.toString()}`)} /></div>
          )}
          <table className="w-full text-sm" aria-label="Ledger batches">
            <caption className="sr-only">Ledger batches list</caption>
            <thead><tr className="bg-gray-50 text-left"><Th>ID</Th><Th>Org</Th><Th>Ts</Th><Th>Source</Th><Th>Posted</Th></tr></thead>
            <tbody>
              {batchesLoading ? (
                <tr><Td colSpan={5}><SkeletonText lines={3} /></Td></tr>
              ) : ((batches?.items||[]).map((b:any)=> (
                <tr key={b.id} className="border-t"><Td>{b.id}</Td><Td>{b.org_id||'—'}</Td><Td>{b.ts||'—'}</Td><Td>{b.source||'—'}</Td><Td>{String(b.posted)}</Td></tr>
              )))}
              {!batchesLoading && !((batches?.items||[]).length) && <tr><Td colSpan={5}><div className="text-gray-500">No batches.</div></Td></tr>}
            </tbody>
          </table>
        </section>

        <section className="bg-white rounded-xl border overflow-hidden">
          <div className="p-3 border-b flex items-center justify-between">
            <h2 className="font-semibold">Entries</h2>
            <div className="flex items-center gap-2 text-xs">
              <label className="flex items-center gap-1">Limit <input className="border rounded px-1 py-0.5 w-16" type="number" value={limitE} onChange={e=>{ const v=Math.max(1, parseInt(e.target.value||'1')); setLimitE(v); setOffsetE(0); }}/></label>
              <button className="px-2 py-1 rounded border bg-white hover:bg-gray-50 disabled:opacity-50" disabled={offsetE<=0 || entriesLoading} onClick={()=> setOffsetE(Math.max(0, offsetE - limitE))}>Prev</button>
              <button className="px-2 py-1 rounded border bg-white hover:bg-gray-50 disabled:opacity-50" disabled={entriesLoading || (entries?.items||[]).length < limitE} onClick={()=> setOffsetE(offsetE + limitE)}>Next</button>
              <span>Page {Math.floor(offsetE/limitE)+1}</span>
            </div>
          </div>
          {entriesError && (
            <div className="p-3"><InlineError message={String((entriesError as any)?.message || entriesError)} onRetry={()=> mutate(`${API_BASE}/finance/ledger/entries?${qsEntries.toString()}`)} /></div>
          )}
          <table className="w-full text-sm" aria-label="Ledger entries">
            <caption className="sr-only">Ledger entries list</caption>
            <thead><tr className="bg-gray-50 text-left"><Th>ID</Th><Th>Batch</Th><Th>Account</Th><Th>Amount</Th><Th>Debit</Th><Th>Ref</Th></tr></thead>
            <tbody>
              {entriesLoading ? (
                <tr><Td colSpan={6}><SkeletonText lines={3} /></Td></tr>
              ) : ((entries?.items||[]).map((e:any)=> (
                <tr key={e.id} className="border-t"><Td>{e.id}</Td><Td>{e.entry_batch_id}</Td><Td>{e.account_id}</Td><Td>${Number(e.amount||0).toFixed(2)}</Td><Td>{String(e.debit)}</Td><Td>{e.ref_type||'—'}</Td></tr>
              )))}
              {!entriesLoading && !((entries?.items||[]).length) && <tr><Td colSpan={6}><div className="text-gray-500">No entries.</div></Td></tr>}
            </tbody>
          </table>
        </section>
      </div>

      {lastReconId && (
        <div className="text-xs text-blue-700">
          View status: <Link className="underline" href={`/finance/recon?task=${lastReconId}`}>{lastReconId}</Link>
        </div>
      )}

      <Modal open={showNewBatch} title="Create Ledger Batch" onClose={()=>setShowNewBatch(false)}>
        {!canWrite ? (
          <div className="text-sm text-red-600">Insufficient role. Login as admin/finance/editor.</div>
        ) : (
          <form onSubmit={createBatch} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Org ID (optional)"><input className="border rounded px-2 py-1 w-full" value={formBatch.org_id||''} onChange={e=>setFormBatch({...formBatch, org_id:e.target.value})} /></Field>
              <Field label="Source"><input className="border rounded px-2 py-1 w-full" value={formBatch.source} onChange={e=>setFormBatch({...formBatch, source:e.target.value})} /></Field>
              <Field label="Posted?">
                <select className="border rounded px-2 py-1 w-full" value={formBatch.posted? 'true':'false'} onChange={e=>setFormBatch({...formBatch, posted: e.target.value==='true'})}>
                  <option value="false">No</option>
                  <option value="true">Yes</option>
                </select>
              </Field>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="px-3 py-1.5 text-sm border rounded" onClick={()=>setShowNewBatch(false)}>Cancel</button>
              <button type="submit" className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white">Create</button>
            </div>
          </form>
        )}
      </Modal>

      <Modal open={showNewEntry} title="Create Ledger Entry" onClose={()=>setShowNewEntry(false)}>
        {!canWrite ? (
          <div className="text-sm text-red-600">Insufficient role. Login as admin/finance/editor.</div>
        ) : (
          <form onSubmit={createEntry} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Batch ID"><input className="border rounded px-2 py-1 w-full" value={formEntry.entry_batch_id} onChange={e=>setFormEntry({...formEntry, entry_batch_id:e.target.value})} required /></Field>
              <Field label="Account ID"><input className="border rounded px-2 py-1 w-full" value={formEntry.account_id} onChange={e=>setFormEntry({...formEntry, account_id:e.target.value})} required /></Field>
              <Field label="Amount"><input type="number" step="0.01" className="border rounded px-2 py-1 w-full" value={formEntry.amount} onChange={e=>setFormEntry({...formEntry, amount:e.target.value})} required /></Field>
              <Field label="Debit?">
                <select className="border rounded px-2 py-1 w-full" value={formEntry.debit? 'true':'false'} onChange={e=>setFormEntry({...formEntry, debit: e.target.value==='true'})}>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </Field>
              <Field label="Ref Type (optional)"><input className="border rounded px-2 py-1 w-full" value={formEntry.ref_type||''} onChange={e=>setFormEntry({...formEntry, ref_type:e.target.value})} /></Field>
              <Field label="Ref ID (optional)"><input className="border rounded px-2 py-1 w-full" value={formEntry.ref_id||''} onChange={e=>setFormEntry({...formEntry, ref_id:e.target.value})} /></Field>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="px-3 py-1.5 text-sm border rounded" onClick={()=>setShowNewEntry(false)}>Cancel</button>
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
