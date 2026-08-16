import React from 'react';
import { LineChart, BarChart3, Activity, ArrowUpRight } from 'lucide-react';

export default function Observability() {
  const metrics = [
    "API Request Rate",
    "API P99 Latency",
    "Routing Decisions",
    "Total Routing Decisions",
    "Embedding P99 Duration",
    "ML Queue Depth",
    "Routing Queue Depth",
    "DLQ Entries"
  ];

  return (
    <section id="observability" className="py-24 bg-slate-900 border-t border-slate-800">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row gap-12 items-center max-w-6xl mx-auto">
          <div className="w-full md:w-1/2">
            <h2 className="text-3xl font-bold text-white mb-6">
              Monitored like a production system.
            </h2>
            <p className="text-lg text-slate-400 mb-8">
              SmartInbox uses a professional observability stack to ensure reliability and performance at scale.
            </p>
            
            <div className="space-y-6 mb-8">
              <div className="flex gap-4">
                <div className="bg-orange-500/10 p-3 rounded-xl h-fit">
                  <Activity className="w-6 h-6 text-orange-500" />
                </div>
                <div>
                  <h4 className="text-white font-semibold text-lg">Prometheus</h4>
                  <p className="text-slate-400">Collects and stores application/system metrics.</p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="bg-blue-500/10 p-3 rounded-xl h-fit">
                  <LineChart className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <h4 className="text-white font-semibold text-lg">Grafana</h4>
                  <p className="text-slate-400">Turns those metrics into real-time dashboards.</p>
                </div>
              </div>
            </div>
            
            <a href="http://localhost:3000" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-medium transition-colors border border-slate-700">
              Open Grafana Dashboard
              <ArrowUpRight className="w-4 h-4" />
            </a>
          </div>
          
          <div className="w-full md:w-1/2">
            <div className="grid grid-cols-2 gap-4">
              {metrics.map((metric, i) => (
                <div key={i} className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex items-center gap-3">
                  <BarChart3 className="w-4 h-4 text-indigo-500 opacity-70" />
                  <span className="text-sm font-medium text-slate-300">{metric}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
