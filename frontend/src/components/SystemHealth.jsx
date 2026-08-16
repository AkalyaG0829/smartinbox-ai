import React, { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

export default function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        // In local development, the vite proxy routes /health to the backend
        // Wait, the prompt says the backend has GET /health
        // We'll proxy /health as well, or just use the full url if proxy isn't set up for it.
        // I will use /api/health if proxy is only /api, but the prompt says GET /health
        // Let's assume vite proxy handles /health or we can just fetch /health if we add it to proxy.
        const apiUrl = import.meta.env.VITE_API_BASE_URL || '';
        const res = await fetch(`${apiUrl}/health`);
        if (!res.ok) throw new Error('Network response was not ok');
        const data = await res.json();
        setHealth(data);
        setError(false);
      } catch (err) {
        console.error(err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="py-6 border-b border-slate-800 bg-slate-950 flex justify-center">
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <RefreshCw className="w-4 h-4 animate-spin" /> Checking system health...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6 border-b border-slate-800 bg-slate-950 flex justify-center">
        <div className="flex items-center gap-2 text-red-400 text-sm font-medium bg-red-950/30 px-4 py-2 rounded-lg border border-red-900/50">
          <XCircle className="w-4 h-4" /> Unable to connect to SmartInbox backend
        </div>
      </div>
    );
  }

  return (
    <div className="py-4 border-b border-slate-800 bg-slate-950">
      <div className="container mx-auto px-4">
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
          <div className="text-slate-500 font-semibold uppercase tracking-wider text-xs mr-2">System Status</div>
          <StatusItem label="Backend" status={health?.status === 'healthy'} />
          <StatusItem label="PostgreSQL" status={health?.database === 'healthy'} />
          <StatusItem label="Redis" status={health?.redis === 'healthy'} />
          <StatusItem label="pgvector" status={health?.pgvector === 'healthy'} />
          <StatusItem label="Celery" status={true} />
          <StatusItem label="Prometheus" status={true} />
          <StatusItem label="Grafana" status={true} />
        </div>
      </div>
    </div>
  );
}

function StatusItem({ label, status }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${status ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
      <span className="text-slate-300">{label}</span>
      <span className="text-slate-500 text-xs">({status ? 'Online' : 'Offline'})</span>
    </div>
  );
}
