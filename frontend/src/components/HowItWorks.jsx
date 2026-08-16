import React from 'react';
import { MessageSquare, Server, Cpu, Database, Network, ArrowDown, Activity } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    { icon: MessageSquare, title: "Incoming Message", desc: "User sends a message payload." },
    { icon: Server, title: "FastAPI API", desc: "Receives REST request and parses schema." },
    { icon: Activity, title: "Celery Task Queue", desc: "Enqueues message for asynchronous processing." },
    { icon: Cpu, title: "ML Processing & Embeddings", desc: "Generates semantic text representations." },
    { icon: Database, title: "PostgreSQL + pgvector", desc: "Stores embeddings and retrieves semantic evidence." },
    { icon: Network, title: "AI Routing Decision", desc: "Heuristics and AI evaluate context." },
    { icon: MessageSquare, title: "Priority Assigned", desc: "Categorized as URGENT, IMPORTANT, DIGEST, or IGNORE." },
  ];

  return (
    <section id="how-it-works" className="py-24 bg-slate-900 border-y border-slate-800">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">How It Works</h2>
          <p className="text-slate-400">
            A look under the hood at the SmartInbox message processing pipeline.
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          {steps.map((step, idx) => (
            <React.Fragment key={idx}>
              <div className="flex items-center gap-6 p-4 rounded-xl bg-slate-950/50 border border-slate-800 hover:border-indigo-500/50 transition-colors">
                <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-indigo-900/30 flex items-center justify-center border border-indigo-500/30">
                  <step.icon className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-lg">{step.title}</h3>
                  <p className="text-slate-400 text-sm">{step.desc}</p>
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div className="flex justify-center py-2">
                  <ArrowDown className="w-5 h-5 text-slate-700" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}
