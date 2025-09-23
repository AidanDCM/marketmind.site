"use client";

import React from "react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { API_BASE, getJson, postJson } from "../../../lib/api";
import { useToast } from "../../../components/ui/Toast";
import { useRole } from "../../../lib/auth";
import { GuardedButton } from "../../../components/ui/GuardedAction";

export default function ReconPage(){
  const toast = useToast();
  const { role, tokenPresent } = useRole();
  const canWrite = !!tokenPresent && ["admin","finance","editor"].includes(role||"");
  const [orgId, setOrgId] = React.useState<string>("");
  const [taskId, setTaskId] = React.useState<string>("");
  const [autoPoll, setAutoPoll] = React.useState<boolean>(true);
  const searchParams = useSearchParams();

  const { data: task, isValidating, mutate } = useSWR<any>(
    taskId ? `${API_BASE}/finance/recon/tasks/${taskId}` : null,
    getJson,
    { refreshInterval: autoPoll ? 2000 : 0 }
  );

  React.useEffect(() => {
    const t = searchParams?.get('task');
    if (t) setTaskId(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  async function startRecon(){
    try{
      const payload: any = {};
      if (orgId) payload.org_id = orgId;
      payload.scope = 'ledger';
      const res = await postJson<{ id: string }>(`/finance/recon/tasks`, payload);
      const id = res?.id || "";
      if (id) {
        setTaskId(id);
        toast.success(`Recon started: ${id}`);
        mutate();
      } else {
        toast.info('Recon task created');
      }
    } catch(e:any){
      toast.error(e?.message || 'Failed to start recon');
    }
  }

  function copyId(){
    try{ if (taskId && typeof navigator !== 'undefined') { navigator.clipboard.writeText(taskId); toast.success('Copied Task ID'); } } catch {}
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Reconciliation</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm">
            <div className="text-gray-600 mb-1">Org ID (optional)</div>
            <input className="border rounded px-2 py-1 w-48" value={orgId} onChange={e=>setOrgId(e.target.value)} />
          </label>
          <GuardedButton allowed={canWrite} className="px-3 py-2 text-sm rounded-md border bg-emerald-600 text-white hover:bg-emerald-700" onClick={startRecon}>
            Start Recon
          </GuardedButton>
        </div>
      </div>

      <div className="mm-card p-4">
        <div className="flex items-center gap-2">
          <label className="text-sm flex-1">
            <div className="text-gray-600 mb-1">Recon Task ID</div>
            <input className="border rounded px-2 py-1 w-full" placeholder="paste task id or start a new one" value={taskId} onChange={e=>setTaskId(e.target.value)} />
          </label>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={()=>mutate()} disabled={!taskId}>Refresh</button>
          <button className="px-2 py-1 text-xs rounded-md border bg-white hover:bg-gray-50" onClick={copyId} disabled={!taskId}>Copy ID</button>
          <label className="text-xs flex items-center gap-1">
            <input type="checkbox" checked={autoPoll} onChange={e=>setAutoPoll(e.target.checked)} /> Auto-poll
          </label>
        </div>
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <Info label="Status" value={task?.status || task?.state || (taskId? (isValidating? 'loading…':'unknown'):'—')} />
          <Info label="Started" value={task?.started_at || task?.created_at || '—'} />
          <Info label="Finished" value={task?.finished_at || task?.done_at || '—'} />
          <Info label="Progress" value={formatProgress(task)} />
        </div>
        <div className="mt-4">
          <pre className="bg-gray-50 p-3 rounded border overflow-auto text-xs max-h-96" aria-label="Recon Task JSON">
{JSON.stringify(task ?? (taskId? { message: 'No data yet' } : { message: 'Start or paste a task id' }), null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }:{ label:string; value: React.ReactNode }){
  return (
    <div className="p-3 bg-white rounded border">
      <div className="text-xs text-gray-600">{label}</div>
      <div className="text-sm font-medium break-all">{value}</div>
    </div>
  );
}

function formatProgress(task:any): string{
  if (!task) return '—';
  const p = task.progress ?? task.percent ?? task.pct;
  if (typeof p === 'number') return `${Math.round(p)}%`;
  return task.progress_text || '—';
}
