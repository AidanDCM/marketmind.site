"use client";

import * as React from "react";
import useSWR, { mutate } from "swr";
import { authHeaders, API_BASE } from "../../lib/api";
import { MetricsChart, Sparkline, DonutChart } from "../../components/charts/MetricsChart";
import { SystemAlerts, AlertBanner } from "../../components/alerts/SystemAlerts";
import { InlineError } from "../../components/ui/InlineError";
import { SkeletonText } from "../../components/ui/Skeleton";
import { useToast } from "../../components/ui/Toast";

const API = API_BASE;
const fetcher = (url: string) => fetch(url, { headers: authHeaders() }).then((r) => r.json());

// Generate mock time series data for charts
function generateMockTimeSeriesData(type: string, hours: number) {
  const data = [];
  const now = new Date();
  
  for (let i = hours; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
    let value = 0;
    
    switch (type) {
      case 'profit':
        value = 15 + Math.sin(i * 0.3) * 5 + Math.random() * 3;
        break;
      case 'orders':
        value = 120 + Math.sin(i * 0.2) * 30 + Math.random() * 20;
        break;
      case 'confidence':
        value = 0.85 + Math.sin(i * 0.1) * 0.1 + Math.random() * 0.05;
        break;
      default:
        value = Math.random() * 100;
    }
    
    data.push({
      timestamp: timestamp.toISOString(),
      value: Math.max(0, value),
      label: `${type} at ${timestamp.toLocaleTimeString()}`
    });
  }
  
  return data;
}

export default function CommandCenterPage() {
  const { data: kpis, error: kpisErr } = useSWR(`${API}/dash/kpis`, fetcher);
  const { data: dashKpis, error: dashKpisErr } = useSWR(`${API}/profit/kpis`, fetcher);
  const { data: profitLog, error: profitErr } = useSWR(`${API}/profit/log?limit=10`, fetcher);
  const { data: health, error: healthErr } = useSWR(`${API}/health/summary`, fetcher);
  const { data: healthData, error: healthDataErr } = useSWR(`${API}/health/data`, fetcher);

  // Normalize KPIs into a list of cards regardless of shape
  const kpiCards = React.useMemo(() => {
    // If API already returns an array of {label,value,trend}
    if (Array.isArray(kpis)) return kpis as any[];
    // If API returns an object (orders, net_revenue, aov)
    if (kpis && typeof kpis === 'object') {
      const list: any[] = [];
      const orders = (kpis as any).orders ?? 0;
      const netRev = (kpis as any).net_revenue ?? (kpis as any).netRevenue ?? 0;
      const aov = (kpis as any).aov ?? 0;
      list.push({ label: 'Orders', value: String(orders), trend: 'stable' });
      list.push({ label: 'Net Revenue', value: `$${Number(netRev).toFixed(2)}`, trend: 'up' });
      list.push({ label: 'AOV', value: `$${Number(aov).toFixed(2)}`, trend: 'stable' });
      return list;
    }
    return [] as any[];
  }, [kpis]);
  const { data: learningModels, error: lmErr } = useSWR(`${API}/learning/models?limit=10`, fetcher);
  const { data: learningMetrics, error: lmetErr } = useSWR(`${API}/learning/metrics?limit=10`, fetcher);
  const { data: rollouts, error: rolloutsErr } = useSWR(`${API}/learning/rollouts?limit=10`, fetcher);
  const { data: integrationsHealth, error: integErr } = useSWR(`${API}/health/integrations`, fetcher);
  const { data: aiDecisions, error: aiErr } = useSWR(`${API}/ai/decisions?limit=10`, fetcher);
  const { data: systemReasons, error: reasonsErr } = useSWR(`${API}/ai/reasoning?limit=8`, fetcher);
  const { success, error: pushError } = useToast();
  const hasError = Boolean(
    kpisErr || dashKpisErr || profitErr || healthErr || healthDataErr || lmErr || lmetErr || rolloutsErr || integErr || aiErr || reasonsErr
  );
  const prevHasErrorRef = React.useRef<boolean>(false);
  React.useEffect(() => {
    if (hasError && !prevHasErrorRef.current) {
      pushError("Some Command Center data is unavailable");
    } else if (!hasError && prevHasErrorRef.current) {
      success("All systems recovered");
    }
    prevHasErrorRef.current = hasError;
  }, [hasError, success, pushError]);
  
  // Auto-refresh every 30 seconds using SWR revalidation
  React.useEffect(() => {
    const interval = setInterval(async () => {
      // Trigger SWR revalidation for all endpoints
      await Promise.all([
        mutate(`${API}/dash/kpis`),
        mutate(`${API}/profit/kpis`),
        mutate(`${API}/profit/log?limit=10`),
        mutate(`${API}/health/summary`),
        mutate(`${API}/health/data`),
        mutate(`${API}/learning/models?limit=10`),
        mutate(`${API}/learning/metrics?limit=10`),
        mutate(`${API}/learning/rollouts?limit=10`),
        mutate(`${API}/health/integrations`),
        mutate(`${API}/ai/decisions?limit=10`),
        mutate(`${API}/ai/reasoning?limit=8`)
      ]);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Modern Header with Glass Effect */}
      <div className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-white/20 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white text-xl font-bold">🧠</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  MarketMind Command Center
                </h1>
                <p className="text-sm text-gray-600">AI-Powered E-commerce Operations Hub</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-white/60 rounded-lg border border-white/30">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700">Live Monitoring</span>
              </div>
              <div className="text-xs text-gray-500 bg-white/40 px-3 py-2 rounded-lg">
                {formatTime(new Date().toISOString())}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-8">
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-8">
        {(kpisErr || dashKpisErr || profitErr || healthErr || healthDataErr || lmErr || lmetErr || rolloutsErr || integErr || aiErr || reasonsErr) && (
          <InlineError
            title="Some Command Center data is unavailable"
            message={String((kpisErr as any)?.message || kpisErr || (dashKpisErr as any)?.message || dashKpisErr || (profitErr as any)?.message || profitErr || (healthErr as any)?.message || healthErr || (healthDataErr as any)?.message || healthDataErr || (lmErr as any)?.message || lmErr || (lmetErr as any)?.message || lmetErr || (rolloutsErr as any)?.message || rolloutsErr || (integErr as any)?.message || integErr || (aiErr as any)?.message || aiErr || (reasonsErr as any)?.message || reasonsErr)}
            onRetry={() => {
              mutate(`${API}/dash/kpis`);
              mutate(`${API}/profit/kpis`);
              mutate(`${API}/profit/log?limit=10`);
              mutate(`${API}/health/summary`);
              mutate(`${API}/health/data`);
              mutate(`${API}/learning/models?limit=10`);
              mutate(`${API}/learning/metrics?limit=10`);
              mutate(`${API}/learning/rollouts?limit=10`);
              mutate(`${API}/health/integrations`);
              mutate(`${API}/ai/decisions?limit=10`);
              mutate(`${API}/ai/reasoning?limit=8`);
            }}
          />
        )}

        {/* Core System Overview */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🧭 Core System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {healthData === undefined ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-white/70 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow animate-pulse">
                  <div className="h-3 w-24 bg-gray-200 rounded mb-2" />
                  <div className="h-8 w-32 bg-gray-100 rounded" />
                </div>
              ))
            ) : (
              <>
                <OverviewCard
                  title="Database"
                  value={healthData?.db?.ok ? 'Healthy' : 'Issue'}
                  subtitle={`${healthData?.db?.latency_ms ?? '—'} ms`}
                  status={healthData?.db?.ok ? 'up' : 'down'}
                />
                {(() => {
                  const configured = Boolean(healthData?.redis?.configured);
                  const ok = Boolean(healthData?.redis?.ok);
                  const latency = healthData?.redis?.latency_ms ?? '—';
                  return (
                    <OverviewCard
                      title="Redis"
                      value={!configured ? 'Disabled' : ok ? 'Healthy' : 'Issue'}
                      subtitle={!configured ? 'Not configured' : `${latency} ms`}
                      status={!configured ? 'stable' : ok ? 'up' : 'down'}
                    />
                  );
                })()}
                <OverviewCard
                  title="Integrations"
                  value={`${Object.values(healthData?.integrations || {}).filter((x:any)=>x?.configured).length}`}
                  subtitle={`Configured of ${Object.keys(healthData?.integrations || {}).length}`}
                  status="stable"
                />
                <OverviewCard
                  title="AI Decisions"
                  value={`${(aiDecisions?.items||[]).length}`}
                  subtitle="Recent window"
                  status="stable"
                />
              </>
            )}
          </div>
        </section>
        {/* KPIs */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Key Performance Indicators</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {kpis === undefined && kpiCards.length === 0 ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={`sk-${i}`} className="bg-white/70 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow animate-pulse">
                  <div className="h-4 w-32 bg-gray-200 rounded mb-3" />
                  <div className="h-8 w-24 bg-gray-100 rounded" />
                </div>
              ))
            ) : (
              kpiCards.map((kpi, index) => (
                <div key={index} className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  <div className="relative bg-white/70 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">{kpi.label}</p>
                        <p className="text-3xl font-bold text-gray-900 mt-2">{kpi.value}</p>
                      </div>
                      <div className={`p-3 rounded-xl shadow-lg ${
                        kpi.trend === 'up' ? 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-white' :
                        kpi.trend === 'down' ? 'bg-gradient-to-br from-red-400 to-red-600 text-white' :
                        'bg-gradient-to-br from-gray-400 to-gray-600 text-white'
                      }`}>
                        {kpi.trend === 'up' ? '📈' : kpi.trend === 'down' ? '📉' : '📊'}
                      </div>
                    </div>
                    {kpi.change && (
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                          kpi.trend === 'up' ? 'bg-emerald-100 text-emerald-700' :
                          kpi.trend === 'down' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {kpi.change}
                        </span>
                        <span className="text-xs text-gray-500 font-medium">vs last period</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Real-time Metrics Charts */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📈 Real-time Performance Metrics</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <MetricsChart
              title="Profit Margin Trend"
              data={React.useMemo(() => generateMockTimeSeriesData('profit', 24), [])}
              color="#10B981"
              height={180}
            />
            <MetricsChart
              title="Order Volume"
              data={React.useMemo(() => generateMockTimeSeriesData('orders', 24), [])}
              color="#3B82F6"
              height={180}
            />
            <MetricsChart
              title="AI Decision Confidence"
              data={React.useMemo(() => generateMockTimeSeriesData('confidence', 24), [])}
              color="#8B5CF6"
              height={180}
            />
          </div>
        </section>

        {/* AI Reasoning Section */}
        <AIReasoningSection aiDecisions={aiDecisions} systemReasons={systemReasons} />

        {/* System Activity */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🔄 System Activity</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Panel title="💡 Latest Profit Module Events" className="h-80">
              <div className="overflow-y-auto h-64">
                {profitLog === undefined ? (
                  <div className="p-3"><SkeletonText lines={6} /></div>
                ) : (
                  <Table
                    headers={["Time", "Module", "Action", "Outcome"]}
                    rows={(profitLog?.items ?? []).map((r: any) => [
                      formatTime(r.timestamp),
                      r.module ?? "–",
                      r.action ?? "–",
                      <OutcomeBadge key={r.id} outcome={r.outcome} />,
                    ])}
                    empty="No profit events yet."
                    caption="Recent profit module events"
                    ariaLabel="Profit events table"
                  />
                )}
              </div>
            </Panel>

            <Panel title="🚀 Deployment Rollouts" className="h-80">
              <div className="space-y-3 overflow-y-auto h-64">
                {rollouts === undefined ? (
                  <div className="p-3"><SkeletonText lines={6} /></div>
                ) : rollouts?.items?.length ? (
                  rollouts.items.map((r: any) => (
                    <div key={r.id} className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 text-sm font-medium">{r.brain_id?.[0]?.toUpperCase()}</span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-900">{r.brain_id}</span>
                          <div className="text-xs text-gray-500">Brain ID</div>
                        </div>
                      </div>
                      <PhaseBadge phase={r.phase} />
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-gray-400">🚀</span>
                    </div>
                    <p className="text-gray-500 text-sm">No active rollouts</p>
                  </div>
                )}
              </div>
            </Panel>
          </div>
        </section>

        {/* Learning & Models with Enhanced Visualizations */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🧠 Machine Learning</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Panel title="📊 Recent Models">
              <div className="space-y-3">
                {learningModels?.items?.length > 0 ? (
                  learningModels.items.slice(0, 5).map((model: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{model.name || `Model ${idx + 1}`}</div>
                        <div className="text-sm text-gray-500">
                          {model.type || 'neural_network'} • {formatTime(model.created_at || new Date().toISOString())}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Sparkline data={[0.7, 0.75, 0.8, 0.85, 0.9]} color="#10B981" width={40} height={20} />
                        <StatusBadge status={model.status || 'active'} />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-2">🤖</div>
                    <p className="text-gray-500 text-sm">No models yet</p>
                  </div>
                )}
              </div>
            </Panel>
            
            <Panel title="📈 Performance Metrics">
              <div className="space-y-3">
                {learningMetrics?.items?.length > 0 ? (
                  learningMetrics.items.slice(0, 5).map((metric: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">{metric.name || `Metric ${idx + 1}`}</div>
                        <div className="text-sm text-gray-500">
                          Value: {metric.value || '0.85'} • {formatTime(metric.timestamp || new Date().toISOString())}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">{metric.value || '85%'}</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-2">
                      <span className="text-green-500">📊</span>
                    </div>
                    <p className="text-gray-500 text-sm">No metrics yet</p>
                  </div>
                )}
              </div>
            </Panel>

            <Panel title="🎯 Model Performance Distribution">
              <div className="flex flex-col items-center space-y-4">
                <DonutChart
                  data={[
                    { label: 'Excellent', value: 45, color: '#10B981' },
                    { label: 'Good', value: 35, color: '#3B82F6' },
                    { label: 'Fair', value: 15, color: '#F59E0B' },
                    { label: 'Poor', value: 5, color: '#EF4444' }
                  ]}
                  size={120}
                  centerText="85%"
                />
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Excellent (45%)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Good (35%)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span>Fair (15%)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span>Poor (5%)</span>
                  </div>
                </div>
              </div>
            </Panel>
          </div>
        </section>

        {/* AI Reasoning & Decision Making */}
        <AIReasoningSection aiDecisions={aiDecisions} systemReasons={systemReasons} />

        {/* Platform Credentials */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🔐 Platform Credentials & API Usage</h2>
          <PlatformCredentialsSection healthData={healthData} integrationsHealth={integrationsHealth} />
        </section>

        {/* System Alerts */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🚨 System Alerts & Notifications</h2>
          <SystemAlerts />
        </section>

        {/* Operator Controls */}
        <OperatorTray />
      </div>
    </div>
  );
}

function OverviewCard({ title, value, subtitle, status }: { title: string; value: React.ReactNode; subtitle?: string; status?: 'up'|'down'|'stable' }) {
  const color = status === 'up' ? 'from-emerald-400 to-emerald-600' : status === 'down' ? 'from-red-400 to-red-600' : 'from-gray-400 to-gray-600';
  return (
    <div className="group relative">
      <div className={`absolute inset-0 bg-gradient-to-r ${color} rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`}></div>
      <div className="relative bg-white/70 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
        <div className="text-sm text-gray-600">{title}</div>
        <div className="text-3xl font-bold text-gray-900 mt-1">{value}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
      </div>
    </div>
  );
}

function AIReasoningSection({ aiDecisions, systemReasons }: { aiDecisions?: any; systemReasons?: any }) {
  // Mock AI reasoning data for demonstration
  const decisions = aiDecisions?.items || [
    {
      id: 1,
      timestamp: new Date(Date.now() - 300000),
      decision: 'Price Optimization',
      reasoning: 'Competitor analysis shows 15% price gap. Market demand stable at current volume. Recommended 8% price increase to maximize profit margin while maintaining conversion rate.',
      confidence: 0.87,
      factors: ['competitor_pricing', 'demand_elasticity', 'inventory_levels'],
      outcome: 'implemented'
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 600000),
      decision: 'Inventory Restock',
      reasoning: 'Sales velocity increased 23% over 7 days. Current stock will deplete in 4 days. Lead time is 6 days. Triggering restock order to prevent stockout.',
      confidence: 0.94,
      factors: ['sales_velocity', 'lead_time', 'demand_forecast'],
      outcome: 'pending'
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 900000),
      decision: 'Marketing Budget Allocation',
      reasoning: 'Google Ads showing 34% higher ROAS than Facebook. Amazon PPC conversion rate declined 12%. Reallocating 40% budget from Facebook to Google Ads.',
      confidence: 0.76,
      factors: ['roas_comparison', 'conversion_rates', 'budget_efficiency'],
      outcome: 'implemented'
    }
  ];

  const reasoningPatterns = systemReasons?.items || [
    { pattern: 'Price Sensitivity Analysis', usage: 'Active', accuracy: '89%' },
    { pattern: 'Demand Forecasting', usage: 'Active', accuracy: '92%' },
    { pattern: 'Competitor Monitoring', usage: 'Active', accuracy: '85%' },
    { pattern: 'Inventory Optimization', usage: 'Active', accuracy: '91%' }
  ];

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">🧠 AI Decision Making & Reasoning</h2>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Panel title="🤖 Recent AI Decisions" className="h-96">
            <div className="space-y-4 overflow-y-auto" style={{ maxHeight: '320px' }}>
              {(decisions || []).map((decision: any) => (
                <div key={decision.id} className="group relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl"></div>
                  <div className="relative border border-purple-200/50 rounded-2xl p-5 bg-gradient-to-r from-purple-50/80 to-indigo-50/80 hover:shadow-lg transition-all duration-300">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                          <span className="text-white text-sm">🧠</span>
                        </div>
                        <div>
                          <h4 className="font-bold text-gray-900 text-sm">{decision.decision}</h4>
                          <div className="text-xs text-gray-500 font-medium">{formatTime(decision.timestamp)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-xs bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full border border-purple-200/50 font-semibold text-purple-700">
                          {Math.round(decision.confidence * 100)}%
                        </div>
                        <StatusBadge status={decision.outcome} />
                      </div>
                    </div>
                  
                    <div className="text-sm text-gray-700 mb-3 leading-relaxed">
                      {decision.reasoning}
                    </div>
                  
                    <div className="flex flex-wrap gap-1">
                      {(decision.factors || []).map((factor: string) => (
                        <span key={factor} className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                          {factor.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
        
        <div>
          <Panel title="🔍 Reasoning Patterns" className="h-96">
            <div className="space-y-3 overflow-y-auto" style={{ maxHeight: '320px' }}>
              {(reasoningPatterns || []).map((pattern: any, idx: number) => (
                <div key={idx} className="p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-100">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-gray-900 text-sm">{pattern.pattern}</span>
                    <StatusBadge status={pattern.usage.toLowerCase()} />
                  </div>
                  <div className="text-xs text-gray-600">
                    Accuracy: <span className="font-mono font-medium">{pattern.accuracy}</span>
                  </div>
                </div>
              ))}
              
              <div className="mt-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-100">
                <h5 className="font-medium text-gray-900 text-sm mb-2">🎯 Current Focus</h5>
                <div className="text-xs text-gray-600 space-y-1">
                  <div>• Optimizing pricing strategies</div>
                  <div>• Monitoring inventory levels</div>
                  <div>• Analyzing competitor moves</div>
                  <div>• Forecasting demand patterns</div>
                </div>
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </section>
  );
}

function KpiCard({ title, value, unit, trend }: { title: string; value: React.ReactNode; unit?: string; trend?: 'up' | 'down' | 'stable' }) {
  const trendIcon = trend === 'up' ? '↗️' : trend === 'down' ? '↘️' : '➡️';
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-500';
  
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-medium text-gray-700 text-sm">{title}</h3>
        <span className={`text-lg ${trendColor}`}>{trendIcon}</span>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <span className="text-3xl font-bold text-gray-900">{value}</span>
          {unit && <span className="text-lg text-gray-500 ml-1">{unit}</span>}
        </div>
      </div>
    </div>
  );
}

function Panel({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`bg-white rounded-xl shadow-sm border border-gray-100 ${className || ''}`}>
      <div className="p-6">
        <h2 className="font-semibold text-gray-900 mb-4">{title}</h2>
        {children}
      </div>
    </section>
  );
}

function Table({ headers, rows, empty, caption, ariaLabel }: { headers: string[]; rows: (string | number | React.ReactNode)[][]; empty?: string; caption?: string; ariaLabel?: string }) {
  return (
    <table className="w-full text-sm" aria-label={ariaLabel || undefined}>
      {caption ? <caption className="sr-only">{caption}</caption> : null}
      <thead>
        <tr className="text-left">
          {headers.map((h) => (
            <th key={h} scope="col" className="py-1 pr-2">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.length ? (
          rows.map((r, idx) => (
            <tr key={idx} className="border-t">
              {r.map((c, i) => (
                <td key={i} className="py-1 pr-2">{typeof c === 'string' || typeof c === 'number' ? String(c) : c}</td>
              ))}
            </tr>
          ))
        ) : (
          <tr>
            <td className="py-2" colSpan={headers.length}>{empty || "No data."}</td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

function StatusBadge({ status }: { status?: string }) {
  const getStatusColor = (s?: string) => {
    if (!s) return 'bg-gray-100 text-gray-600';
    if (s === 'healthy' || s === 'trained' || s === 'active') return 'bg-green-100 text-green-700';
    if (s === 'warning' || s === 'training') return 'bg-yellow-100 text-yellow-700';
    if (s === 'error' || s === 'failed') return 'bg-red-100 text-red-700';
    return 'bg-blue-100 text-blue-700';
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
      {status || 'unknown'}
    </span>
  );
}

function OutcomeBadge({ outcome }: { outcome?: string }) {
  const getOutcomeColor = (o?: string) => {
    if (!o) return 'bg-gray-100 text-gray-600';
    if (o.toLowerCase().includes('success') || o.toLowerCase().includes('approved')) return 'bg-green-100 text-green-700';
    if (o.toLowerCase().includes('warning') || o.toLowerCase().includes('pending')) return 'bg-yellow-100 text-yellow-700';
    if (o.toLowerCase().includes('error') || o.toLowerCase().includes('failed')) return 'bg-red-100 text-red-700';
    return 'bg-blue-100 text-blue-700';
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getOutcomeColor(outcome)}`}>
      {outcome || '–'}
    </span>
  );
}

function PhaseBadge({ phase }: { phase?: string }) {
  const getPhaseColor = (p?: string) => {
    if (p === 'prod') return 'bg-green-100 text-green-700';
    if (p === 'canary') return 'bg-yellow-100 text-yellow-700';
    if (p === 'shadow') return 'bg-gray-100 text-gray-600';
    return 'bg-blue-100 text-blue-700';
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPhaseColor(phase)}`}>
      {phase || 'unknown'}
    </span>
  );
}

function formatTime(timestamp?: string | Date): string {
  if (!timestamp) return '–';
  try {
    const d = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return d.toLocaleTimeString();
  } catch {
    return String(timestamp);
  }
}

function PlatformCredentialsSection({ healthData, integrationsHealth }: { healthData?: any; integrationsHealth?: any }) {
  // Map backend keys to display info
  const keyMap: Record<string, { name: string; icon: string; credentials: string[] }> = {
    amazon_sp_api: { name: 'Amazon SP-API', icon: '🛒', credentials: ['CLIENT_ID','CLIENT_SECRET','REFRESH_TOKEN','ROLE_ARN'] },
    ebay:          { name: 'eBay',           icon: '🏪', credentials: ['APP_ID','CERT_ID','DEV_ID','USER_TOKEN'] },
    walmart:       { name: 'Walmart',        icon: '🏬', credentials: ['CLIENT_ID','CLIENT_SECRET'] },
    cj:            { name: 'Commission Junction', icon: '💼', credentials: ['API_KEY','WEBSITE_ID'] },
    autods:        { name: 'AutoDS',         icon: '🤖', credentials: ['API_KEY'] },
    keepa:         { name: 'Keepa',          icon: '📈', credentials: ['API_KEY'] },
    gtrends:       { name: 'Google Trends',  icon: '📊', credentials: [] },
  };

  const integrations = healthData?.integrations || {};
  // integrationsHealth could be an object keyed by integration, or an array. Normalize to array of entries with metadata
  const healthEntries: Array<any> = Array.isArray(integrationsHealth)
    ? integrationsHealth
    : integrationsHealth && typeof integrationsHealth === 'object'
      ? Object.keys(integrationsHealth).map((k) => ({ key: k, ...(integrationsHealth as any)[k] }))
      : [];

  const platforms = Object.keys(keyMap).map((key) => {
    const meta = keyMap[key];
    const configured = !!integrations[key]?.configured;
    // Try to find matching health entry
    const he = healthEntries.find((e) => (e.key || e.name)?.toLowerCase()?.includes(key.replace('_', '')) ) || {};
    const status = configured ? (he.status || 'active') : 'missing';
    return {
      key,
      name: meta.name,
      icon: meta.icon,
      status,
      lastCall: he.last_probe || he.last_checked || '—',
      callsToday: he.calls_today ?? he.callsToday ?? 0,
      rateLimit: he.rate_limit || he.rateLimit || '—',
      remaining: he.remaining ?? he.remaining_quota ?? 0,
      latencyMs: he.latency_ms ?? he.latencyMs,
      message: he.message,
      credentials: meta.credentials,
    };
  });

  const recentCalls = (integrationsHealth?.recent_calls || integrationsHealth?.calls || []) as any[];

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">🔐 Platform Credentials & API Usage</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {platforms.map((platform) => (
          <PlatformCard key={platform.name} platform={platform} />
        ))}
      </div>

      <Panel title="📡 Recent API Calls">
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {recentCalls.length ? recentCalls.map((call: any, idx: number) => (
            <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
              <div className="flex items-center gap-2">
                <StatusBadge status={call.status === 200 ? 'success' : 'error'} />
                <span className="font-medium">{call.platform || call.integration || 'API'}</span>
                <span className="text-gray-600">{call.endpoint || call.path || ''}</span>
              </div>
              <span className="text-xs text-gray-500">
                {formatTime(call.timestamp || call.time || call.ts)}
              </span>
            </div>
          )) : (
            <div className="text-xs text-gray-500 p-2">No recent API calls.</div>
          )}
        </div>
      </Panel>
    </section>
  );
}

function PlatformCard({ platform }: { platform: any }) {
  const getStatusColor = (status: string) => {
    if (status === 'active') return 'bg-green-100 text-green-700 border-green-200';
    if (status === 'sandbox') return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    if (status === 'error') return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const utilizationPercent = Math.round(((platform.callsToday) / (platform.remaining + platform.callsToday)) * 100);

  return (
    <div className={`border rounded p-4 bg-white shadow-sm ${getStatusColor(platform.status)}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{platform.icon}</span>
          <div>
            <h3 className="font-medium text-sm">{platform.name}</h3>
            <StatusBadge status={platform.status} />
          </div>
        </div>
      </div>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span>Last Call:</span>
          <span className="font-mono">{platform.lastCall}</span>
        </div>
        {platform.latencyMs !== undefined && (
          <div className="flex justify-between">
            <span>Latency:</span>
            <span className="font-mono">{platform.latencyMs} ms</span>
          </div>
        )}
        <div className="flex justify-between">
          <span>Today:</span>
          <span className="font-mono">{platform.callsToday} calls</span>
        </div>
        <div className="flex justify-between">
          <span>Rate Limit:</span>
          <span className="font-mono">{platform.rateLimit}</span>
        </div>
        <div className="flex justify-between">
          <span>Remaining:</span>
          <span className="font-mono">{platform.remaining}</span>
        </div>
        {platform.message && (
          <div className="text-[11px] text-gray-600 mt-1">{platform.message}</div>
        )}
        
        <div className="mt-2">
          <div className="flex justify-between text-xs mb-1">
            <span>Utilization</span>
            <span>{utilizationPercent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${utilizationPercent > 80 ? 'bg-red-500' : utilizationPercent > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
              style={{ width: `${utilizationPercent}%` }}
            ></div>
          </div>
        </div>

        <div className="mt-2 pt-2 border-t">
          <div className="text-xs text-gray-600">Credentials:</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {platform.credentials.map((cred: string) => (
              <span key={cred} className="px-1 py-0.5 bg-gray-100 rounded text-xs">
                {cred}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function OperatorTray() {
  const [message, setMessage] = React.useState<string>("");

  async function promoteToCanary() {
    setMessage("");
    try {
      const res = await fetch(`${API}/learning/rollouts/promote`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ rollout_id: 1, target_phase: "canary", target_percent: 10 }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || `HTTP ${res.status}`);
      setMessage("Promote to canary accepted.");
    } catch (e: any) {
      setMessage(`Promote error: ${e?.message || String(e)}`);
    }
  }

  async function trainHistorical() {
    setMessage("");
    try {
      const res = await fetch(`${API}/learning/train/historical`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          brain_id: "pricing",
          start_date: "2024-01-01T00:00:00Z",
          end_date: "2024-01-31T23:59:59Z",
          features: ["price", "clicks"],
          model_type: "auto",
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || `HTTP ${res.status}`);
      setMessage("Historical train accepted.");
    } catch (e: any) {
      setMessage(`Train error: ${e?.message || String(e)}`);
    }
  }

  return (
    <section className="border rounded p-4 space-y-3 bg-white shadow-sm">
      <h2 className="font-medium">🎮 Operator Actions</h2>
      <div className="flex gap-2 items-center">
        <button onClick={promoteToCanary} className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded transition-colors">🚀 Promote to Canary</button>
        <button onClick={trainHistorical} className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded transition-colors">🧠 Train Historical</button>
        {message && <span className="text-sm">{message}</span>}
      </div>
      <p className="text-xs text-gray-600">Note: Actions require a valid token (set NEXT_PUBLIC_API_TOKEN or localStorage('api_token')).</p>
    </section>
  );
}
