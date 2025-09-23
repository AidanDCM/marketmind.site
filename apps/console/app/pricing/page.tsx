"use client";
import useSWR from "swr";
import { getJson, postJson, API_BASE } from "../../lib/api";
import React, { useState } from "react";
import { useRole } from "../../lib/auth";
import { GuardedButton } from "../../components/ui/GuardedAction";
import { useToast } from "../../components/ui/Toast";
import { InlineError } from "../../components/ui/InlineError";
import { Th, Td } from "../../components/ui/Table";
import { downloadCsv } from "../../lib/csv";

function Badge({ ok, label }: { ok: boolean; label: string }){
  return (
    <span style={{
      display:'inline-block', padding:'4px 8px', borderRadius:8,
      background: ok? '#E6FFFA':'#FFF5F5', color: ok? '#0F766E':'#9B1C1C',
      fontSize:12, marginRight:8, marginBottom:8, border:'1px solid #ddd'
    }}>{label}: {ok? 'OK':'FAIL'}</span>
  );
}

function fmt(t?: string): string {
  if (!t) return '—';
  try { return new Date(t).toLocaleString(); } catch { return String(t); }
}

export default function PricingLab(){
  const { role, tokenPresent } = useRole();
  const canWrite = !!tokenPresent && ["admin","finance","editor"].includes(role||"");
  const toast = useToast();
  const { data: health, error: healthErr } = useSWR<any>(`${API_BASE}/health/data`, getJson);
  const { data: integrations, error: integErr } = useSWR<any>(`${API_BASE}/health/integrations`, getJson);
  const { data: pending, mutate, error: pendingErr } = useSWR<any>(`${API_BASE}/pricing/pending?limit=100`, getJson, { refreshInterval: 30000 });
  const { data: approved, mutate: mutateApproved, error: approvedErr } = useSWR<any>(`${API_BASE}/pricing/approved?limit=100`, getJson);
  const [simLimit, setSimLimit] = useState<number>(150);
  const [simBusy, setSimBusy] = useState(false);
  const [approveBusyId, setApproveBusyId] = useState<number|undefined>();
  const [pushBusyId, setPushBusyId] = useState<number|undefined>();
  const [exportBusy, setExportBusy] = useState<string|undefined>();
  const [exportMsg, setExportMsg] = useState<string|undefined>();
  const [approveAllBusy, setApproveAllBusy] = useState(false);
  const [bulkMsg, setBulkMsg] = useState<string|undefined>();

  // Guardrails editor state
  const [minNetMarginPct, setMinNetMarginPct] = useState<number>(15);
  const [maxUndercutStep, setMaxUndercutStep] = useState<number>(0.5);
  const [respectMAP, setRespectMAP] = useState<boolean>(true);
  const [freeShippingEnabled, setFreeShippingEnabled] = useState<boolean>(true);
  const [platformFeePct, setPlatformFeePct] = useState<number>(15);
  const [returnReservePct, setReturnReservePct] = useState<number>(2);
  const [estShippingFlat, setEstShippingFlat] = useState<number>(4);

  async function runSim(){
    try{
      setSimBusy(true);
      await postJson(`/pricing/simulate`, {
        limit: simLimit,
        min_net_margin_pct: minNetMarginPct,
        max_undercut_step: maxUndercutStep,
        respect_map: respectMAP,
        free_shipping_enabled: freeShippingEnabled,
        platform_fee_pct: platformFeePct,
        return_reserve_pct: returnReservePct,
        est_shipping_flat: estShippingFlat,
      });
      await mutate();
      await mutateApproved();
      toast.success("Simulation started");
    } catch(e:any){
      toast.error(`Sim failed: ${e?.message||e}`);
    } finally { setSimBusy(false); }
  }

  async function approveProduct(product_id: number){
    try{
      setApproveBusyId(product_id);
      await postJson(`/pricing/approve`, { product_id });
      await mutate();
      await mutateApproved();
      toast.success(`Approved ${product_id}`);
    } finally { setApproveBusyId(undefined); }
  }

  async function unapproveProduct(product_id: number){
    try{
      setApproveBusyId(product_id);
      await postJson(`/pricing/unapprove`, { product_id });
      await mutate();
      await mutateApproved();
      toast.info(`Undid ${product_id}`);
    } finally { setApproveBusyId(undefined); }
  }

  async function pushEbay(product_id: number){
    try{
      setPushBusyId(product_id);
      await postJson(`/pricing/push/ebay?product_id=${product_id}`);
      await mutateApproved();
      toast.success(`Pushed ${product_id} to eBay (dry run)`);
    } finally { setPushBusyId(undefined); }
  }

  async function exportApproved(){
    try{
      setExportBusy('approved'); setExportMsg(undefined);
      const res: any = await postJson(`/pricing/export/approved-to-sheets`);
      setExportMsg(res?.ok ? `Exported ${res.rows} rows to ${res.tab}` : `Export failed: ${res?.reason||'unknown'}`);
      toast[res?.ok? 'success':'error'](res?.ok? `Exported ${res.rows}` : `Export failed`);
    } finally { setExportBusy(undefined); }
  }

  async function exportInventory(){
    try{
      setExportBusy('inventory'); setExportMsg(undefined);
      const res: any = await postJson(`/pricing/export/inventory-to-sheets`);
      setExportMsg(res?.ok ? `Exported ${res.rows} rows to ${res.tab}` : `Export failed: ${res?.reason||'unknown'}`);
      toast[res?.ok? 'success':'error'](res?.ok? `Exported ${res.rows}` : `Export failed`);
    } finally { setExportBusy(undefined); }
  }

  function exportPendingCsv(){
    const items: any[] = (pending?.pending || []);
    const headers = ["product_id","sku","asin","title","proposed_price","margin_pct","created_at"];
    const rows = items.map(r => [r.product_id, r.sku, r.asin, r.title, r.proposed_price, r.margin_pct, r.created_at]);
    downloadCsv("pending_proposals", headers, rows);
  }

  function exportApprovedCsvLocal(){
    const items: any[] = (approved?.approved || []);
    const headers = ["product_id","sku","asin","title","proposed_price","margin_pct","created_at"];
    const rows = items.map(r => [r.product_id, r.sku, r.asin, r.title, r.proposed_price, r.margin_pct, r.created_at]);
    downloadCsv("approved_proposals", headers, rows);
  }

  async function approveAll(){
    const items: any[] = (pending?.pending || []);
    if (!items.length) return;
    if (!confirm(`Approve ${items.length} pending proposals?`)) return;
    try{
      setApproveAllBusy(true);
      setBulkMsg('Starting…');
      let done = 0;
      for (const row of items){
        try { await postJson(`/pricing/approve`, { product_id: row.product_id }); } catch {}
        done++;
        if (done % 10 === 0) setBulkMsg(`Processing… ${done}/${items.length}`);
      }
      await mutate();
      await mutateApproved();
      setBulkMsg(`Approved ${items.length}/${items.length}.`);
      toast.success(`Approved ${items.length} items`);
    } finally {
      setApproveAllBusy(false);
    }
  }

  return (
    <main style={{padding:24, maxWidth:1200, margin:'0 auto'}}>
      <h1 style={{marginBottom:16}}>Pricing Lab</h1>

      <section className="mm-card p-4" style={{marginBottom:24}}>
        <h2>Health</h2>
        <div style={{display:'flex', flexWrap:'wrap'}}>
          <Badge ok={!!health?.db?.ok} label="DB" />
          <Badge ok={!!health?.redis?.ok} label="Redis" />
          <Badge ok={!!health?.integrations?.amazon_sp_api?.configured} label="Amazon SP-API" />
          <Badge ok={!!health?.integrations?.ebay?.configured} label="eBay" />
          <Badge ok={!!health?.integrations?.walmart?.configured} label="Walmart" />
          <Badge ok={!!health?.integrations?.cj?.configured} label="CJ" />
          <Badge ok={!!health?.integrations?.autods?.configured} label="AutoDS" />
          <Badge ok={!!health?.integrations?.keepa?.configured} label="Keepa" />
          <Badge ok={!!health?.integrations?.gtrends?.configured} label="GTrends" />
        </div>
      </section>

      <section className="mm-card p-4" style={{marginTop:24}}>
        <h2 style={{marginBottom:8}}>Pricing Lab (Simulation)</h2>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8, gap:12, flexWrap:'wrap'}}>
          <div className="text-sm text-gray-600" />
          <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
            <button onClick={exportPendingCsv} className="mm-btn">Export Pending CSV</button>
            <GuardedButton allowed={canWrite} onClick={approveAll} className="mm-btn">{approveAllBusy? 'Approving...':'Approve All'}</GuardedButton>
          </div>
        </div>
        <div style={{display:'flex', gap:16, flexWrap:'wrap', alignItems:'center', marginBottom:12}}>
          <label>Limit <input type="number" value={simLimit} onChange={e=>setSimLimit(parseInt(e.target.value||'0'))} style={{width:80}}/></label>
          <label>Min Margin % <input type="number" value={minNetMarginPct} onChange={e=>setMinNetMarginPct(parseFloat(e.target.value||'0'))} style={{width:80}}/></label>
          <label>Undercut $ <input type="number" value={maxUndercutStep} onChange={e=>setMaxUndercutStep(parseFloat(e.target.value||'0'))} style={{width:80}}/></label>
          <label>Platform Fee % <input type="number" value={platformFeePct} onChange={e=>setPlatformFeePct(parseFloat(e.target.value||'0'))} style={{width:80}}/></label>
          <label>Return Reserve % <input type="number" value={returnReservePct} onChange={e=>setReturnReservePct(parseFloat(e.target.value||'0'))} style={{width:80}}/></label>
          <label>Est Shipping $ <input type="number" value={estShippingFlat} onChange={e=>setEstShippingFlat(parseFloat(e.target.value||'0'))} style={{width:80}}/></label>
          <label><input type="checkbox" checked={freeShippingEnabled} onChange={e=>setFreeShippingEnabled(e.target.checked)}/> Free Shipping</label>
          <label><input type="checkbox" checked={respectMAP} onChange={e=>setRespectMAP(e.target.checked)}/> Respect MAP</label>
          <GuardedButton allowed={canWrite} onClick={runSim} className={`mm-btn ${simBusy ? '' : 'primary'}`}>{simBusy? 'Running...':'Run Simulation'}</GuardedButton>
        </div>
        {pending === undefined && (
          <div style={{padding:12, color:'#555'}}>Loading pending proposals…</div>
        )}
        {pendingErr && (
          <div className="mb-3"><InlineError message={String((pendingErr as any)?.message || pendingErr)} /></div>
        )}
        {bulkMsg && (
          <div style={{padding:8, color:'#444'}}>{bulkMsg}</div>
        )}
        <div style={{overflowX:'auto'}}>
          <table className="w-full border-collapse text-sm" aria-label="Pending pricing proposals">
            <caption className="sr-only">Pending pricing proposals</caption>
            <thead>
              <tr>
                <Th className="text-left bg-gray-50">Product ID</Th>
                <Th className="text-left bg-gray-50">SKU</Th>
                <Th className="text-left bg-gray-50">ASIN</Th>
                <Th className="text-left bg-gray-50">Title</Th>
                <Th className="text-left bg-gray-50">Proposed</Th>
                <Th className="text-left bg-gray-50">Margin %</Th>
                <Th className="text-left bg-gray-50">Created</Th>
                <Th className="text-left bg-gray-50">Approve</Th>
              </tr>
            </thead>
            <tbody>
              {(pending?.pending||[]).map((row:any, idx:number)=> (
                <tr key={idx} className="border-t">
                  <Td>{row.product_id}</Td>
                  <Td>{row.sku}</Td>
                  <Td className="max-w-[320px] overflow-hidden text-ellipsis whitespace-nowrap" title={row.asin}>{row.asin || '—'}</Td>
                  <Td className="max-w-[320px] overflow-hidden text-ellipsis whitespace-nowrap" title={row.title}>{row.title}</Td>
                  <Td>${row.proposed_price?.toFixed?.(2) ?? row.proposed_price}</Td>
                  <Td>{row.margin_pct?.toFixed?.(2) ?? row.margin_pct}%</Td>
                  <Td>{fmt(row.created_at)}</Td>
                  <Td><GuardedButton allowed={canWrite} onClick={()=>approveProduct(row.product_id)} className="mm-btn">{approveBusyId===row.product_id? 'Approving...':'Approve'}</GuardedButton></Td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!pending || (pending.pending||[]).length===0) && (
            <div style={{padding:12, color:'#555'}}>No pending proposals yet.</div>
          )}
        </div>
      </section>

    <section className="mm-card p-4" style={{marginTop:24}}>
      <h2 style={{marginBottom:8}}>Approved Proposals</h2>
      <div style={{display:'flex', gap:12, alignItems:'center', marginBottom:8, flexWrap:'wrap'}}>
        <GuardedButton allowed={canWrite} onClick={exportApproved} className="mm-btn">{exportBusy==='approved'? 'Exporting...':'Export Approved → Sheets'}</GuardedButton>
        <GuardedButton allowed={canWrite} onClick={exportInventory} className="mm-btn">{exportBusy==='inventory'? 'Exporting...':'Export Inventory → Sheets'}</GuardedButton>
        <button onClick={exportApprovedCsvLocal} className="mm-btn">Export Approved CSV</button>
        {exportMsg && <span style={{color:'#555'}}>{exportMsg}</span>}
      </div>
      {approved === undefined && (
        <div style={{padding:12, color:'#555'}}>Loading approved proposals…</div>
      )}
      {approvedErr && (<div className="mb-3"><InlineError message={String((approvedErr as any)?.message || approvedErr)} /></div>)}
      <div style={{overflowX:'auto'}}>
        <table className="w-full border-collapse text-sm" aria-label="Approved pricing proposals">
          <caption className="sr-only">Approved pricing proposals</caption>
          <thead>
            <tr>
              <Th className="text-left bg-gray-50">Product ID</Th>
              <Th className="text-left bg-gray-50">SKU</Th>
              <Th className="text-left bg-gray-50">ASIN</Th>
              <Th className="text-left bg-gray-50">Title</Th>
              <Th className="text-left bg-gray-50">Proposed</Th>
              <Th className="text-left bg-gray-50">Margin %</Th>
              <Th className="text-left bg-gray-50">Created</Th>
              <Th className="text-left bg-gray-50">Actions</Th>
            </tr>
          </thead>
          <tbody>
            {approved?.approved?.map((row:any)=>(
              <tr key={`ap-${row.product_id}`} className="border-t">
                <Td>{row.product_id}</Td>
                <Td>{row.sku}</Td>
                <Td>{row.asin}</Td>
                <Td>{row.title}</Td>
                <Td>${row.proposed_price?.toFixed?.(2) ?? row.proposed_price}</Td>
                <Td>{row.margin_pct?.toFixed?.(2) ?? row.margin_pct}%</Td>
                <Td>{fmt(row.created_at)}</Td>
                <Td>
                  <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
                    <GuardedButton allowed={canWrite} onClick={()=>pushEbay(row.product_id)} className="mm-btn">{pushBusyId===row.product_id? 'Pushing...':'Push eBay (Dry Run)'}</GuardedButton>
                    <GuardedButton allowed={canWrite} onClick={()=>unapproveProduct(row.product_id)} className="mm-btn">{approveBusyId===row.product_id? 'Undoing...':'Undo'}</GuardedButton>
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>

      <section className="mm-card p-4">
        <h2>Pricing Lab (SIM)</h2>
        <div style={{display:'flex', alignItems:'center', gap:12, marginBottom:12}}>
          <label>Batch size:</label>
          <input type="number" value={simLimit} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setSimLimit(parseInt(e.target.value||'0'))} style={{width:100, padding:6}} />
          <GuardedButton allowed={canWrite} onClick={runSim} className={`mm-btn ${simBusy ? '' : 'primary'}`}>
            {simBusy? 'Running...':'Run Simulation'}
          </GuardedButton>
        </div>
        <div style={{overflowX:'auto'}}>
          <table className="w-full border-collapse text-sm" aria-label="SIM proposals">
            <caption className="sr-only">SIM proposals</caption>
            <thead>
              <tr>
                <Th className="text-left bg-gray-50">SKU</Th>
                <Th className="text-left bg-gray-50">ASIN</Th>
                <Th className="text-left bg-gray-50">Title</Th>
                <Th className="text-left bg-gray-50">Proposed</Th>
                <Th className="text-left bg-gray-50">Margin %</Th>
                <Th className="text-left bg-gray-50">Created</Th>
                <Th className="text-left bg-gray-50">Approve</Th>
              </tr>
            </thead>
            <tbody>
              {(pending?.pending||[]).map((row:any, idx:number)=> (
                <tr key={idx} className="border-t">
                  <Td>{row.sku}</Td>
                  <Td>{row.asin||'-'}</Td>
                  <Td className="max-w-[320px] overflow-hidden text-ellipsis whitespace-nowrap" title={row.title}>{row.title}</Td>
                  <Td>${row.proposed_price?.toFixed?.(2) ?? row.proposed_price}</Td>
                  <Td>{row.margin_pct?.toFixed?.(2) ?? row.margin_pct}%</Td>
                  <Td>{fmt(row.created_at)}</Td>
                  <Td><button onClick={()=>approveProduct(row.product_id)} disabled={approveBusyId===row.product_id} className="mm-btn">{approveBusyId===row.product_id? 'Approving...':'Approve'}</button></Td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!pending || (pending.pending||[]).length===0) && (
            <div style={{padding:12, color:'#555'}}>No pending proposals yet.</div>
          )}
        </div>
      </section>
    </main>
  );
}

// Removed inline th/td/table styles in favor of shared <Th>/<Td> with Tailwind classes
