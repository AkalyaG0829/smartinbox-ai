import React from 'react';
import { Inbox } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="py-12 bg-slate-950 border-t border-slate-900">
      <div className="container mx-auto px-4 flex flex-col items-center text-center">
        <div className="flex items-center gap-2 mb-4">
          <div className="bg-indigo-600 p-1.5 rounded-lg">
            <Inbox className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg text-white">SmartInbox</span>
        </div>
        
        <p className="text-slate-400 mb-8 max-w-sm">
          AI-powered message intelligence and routing. Built for intelligent communication.
        </p>

        <div className="flex flex-wrap justify-center gap-3 max-w-2xl mb-8">
          {['FastAPI', 'React', 'Celery', 'Redis', 'PostgreSQL', 'pgvector', 'Prometheus', 'Grafana'].map((tech, i) => (
            <span key={i} className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-medium text-slate-400">
              {tech}
            </span>
          ))}
        </div>
        
        <div className="text-xs text-slate-600">
          &copy; {new Date().getFullYear()} SmartInbox AI Project.
        </div>
      </div>
    </footer>
  );
}
