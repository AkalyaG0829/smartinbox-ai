import React from 'react';
import { Server, Database, Activity, HardDrive, BarChart3, Repeat } from 'lucide-react';

export default function Architecture() {
  return (
    <section id="architecture" className="py-24 bg-slate-950">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Architecture</h2>
          <p className="text-slate-400">
            SmartInbox is built on a scalable, modern technology stack.
          </p>
        </div>

        <div className="max-w-4xl mx-auto p-8 rounded-3xl bg-slate-900 border border-slate-800 overflow-x-auto">
          <div className="min-w-[700px] flex flex-col items-center gap-8">
            {/* Client */}
            <div className="px-8 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" />
              Client
            </div>
            
            <div className="h-8 w-px bg-slate-700"></div>
            
            {/* FastAPI */}
            <div className="px-12 py-4 rounded-xl bg-indigo-950/40 border border-indigo-900/50 text-white font-bold flex flex-col items-center w-64">
              <Server className="w-6 h-6 text-indigo-400 mb-2" />
              FastAPI
            </div>
            
            <div className="h-8 w-px bg-slate-700"></div>
            
            {/* Data Layer */}
            <div className="flex gap-16 w-full justify-center">
              <div className="flex flex-col items-center">
                <div className="px-8 py-4 rounded-xl bg-red-950/20 border border-red-900/30 text-white font-semibold flex flex-col items-center w-48">
                  <HardDrive className="w-6 h-6 text-red-400 mb-2" />
                  Redis
                </div>
                <div className="h-8 w-px bg-slate-700"></div>
                <div className="px-16 py-4 rounded-xl bg-orange-950/20 border border-orange-900/30 text-white font-bold flex flex-col items-center w-[300px]">
                  <Repeat className="w-6 h-6 text-orange-400 mb-2" />
                  Celery Workers
                  <div className="flex gap-4 mt-3 text-xs text-slate-300 font-normal">
                    <span className="bg-slate-800 px-2 py-1 rounded">ML Worker</span>
                    <span className="bg-slate-800 px-2 py-1 rounded">Routing Worker</span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-center">
                <div className="px-8 py-4 rounded-xl bg-blue-950/20 border border-blue-900/30 text-white font-semibold flex flex-col items-center w-48 h-[120px] justify-center">
                  <Database className="w-6 h-6 text-blue-400 mb-2" />
                  PostgreSQL
                  <span className="text-xs text-blue-300 font-normal">+ pgvector</span>
                </div>
              </div>
            </div>

            <div className="w-full flex justify-center pt-8 border-t border-slate-800 mt-4 gap-8">
               <div className="flex items-center gap-2 text-sm text-slate-400">
                  <BarChart3 className="w-4 h-4 text-emerald-500" />
                  Prometheus → Grafana
               </div>
               <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Activity className="w-4 h-4 text-rose-500" />
                  Redis → DLQ Metrics
               </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
