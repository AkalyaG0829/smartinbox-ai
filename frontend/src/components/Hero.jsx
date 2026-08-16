import React from 'react';
import { ArrowRight, BrainCircuit, Inbox, Activity } from 'lucide-react';

export default function Hero() {
  const scrollToDemo = () => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' });
  const scrollToArch = () => document.getElementById('architecture')?.scrollIntoView({ behavior: 'smooth' });

  return (
    <section className="relative pt-24 pb-32 overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-900/20 blur-[120px] rounded-full pointer-events-none"></div>
      
      <div className="container mx-auto px-4 relative z-10 flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/50 border border-slate-800 text-indigo-400 text-sm font-medium mb-8">
          <BrainCircuit className="w-4 h-4" />
          <span>SmartInbox version 2.0</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight leading-tight mb-6 max-w-4xl">
          Your Inbox.<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Understood by AI.</span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-10 leading-relaxed">
          SmartInbox automatically understands, prioritizes, and routes incoming messages so important information gets attention at the right time.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-20">
          <button onClick={scrollToDemo} className="w-full sm:w-auto flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-8 py-3.5 rounded-xl transition-all shadow-lg hover:shadow-indigo-600/25">
            Try Live Demo
            <ArrowRight className="w-4 h-4" />
          </button>
          <button onClick={scrollToArch} className="w-full sm:w-auto flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white font-medium px-8 py-3.5 rounded-xl transition-all border border-slate-700">
            View Architecture
          </button>
        </div>

        {/* Visual Illustration */}
        <div className="w-full max-w-4xl mx-auto">
          <div className="relative rounded-2xl border border-slate-800 bg-slate-900/50 p-4 md:p-8 backdrop-blur-sm shadow-2xl">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              {/* Inbox */}
              <div className="w-full md:w-1/3 flex flex-col gap-3">
                <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 text-left">Incoming</div>
                <div className="bg-slate-800 p-3 rounded-lg border border-slate-700 opacity-60">
                  <div className="h-2 w-3/4 bg-slate-600 rounded mb-2"></div>
                  <div className="h-2 w-1/2 bg-slate-600 rounded"></div>
                </div>
                <div className="bg-slate-800 p-3 rounded-lg border border-slate-700 opacity-80">
                  <div className="h-2 w-full bg-slate-600 rounded mb-2"></div>
                  <div className="h-2 w-2/3 bg-slate-600 rounded"></div>
                </div>
                <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                  <div className="h-2 w-5/6 bg-slate-600 rounded mb-2"></div>
                  <div className="h-2 w-1/3 bg-slate-600 rounded"></div>
                </div>
              </div>

              {/* AI Engine */}
              <div className="flex-shrink-0 flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-indigo-500 rounded-full blur-xl opacity-30 animate-pulse"></div>
                  <div className="relative bg-indigo-600 w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3">
                    <BrainCircuit className="w-8 h-8 text-white" />
                  </div>
                </div>
              </div>

              {/* Routed */}
              <div className="w-full md:w-1/3 flex flex-col gap-3">
                <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 text-left">Routed</div>
                <div className="flex items-center gap-3 bg-red-950/40 p-3 rounded-lg border border-red-900/50">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <div className="flex-1 h-2 bg-slate-700 rounded"></div>
                  <span className="text-[10px] font-bold text-red-400 uppercase">Urgent</span>
                </div>
                <div className="flex items-center gap-3 bg-orange-950/40 p-3 rounded-lg border border-orange-900/50">
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  <div className="flex-1 h-2 bg-slate-700 rounded"></div>
                  <span className="text-[10px] font-bold text-orange-400 uppercase">Important</span>
                </div>
                <div className="flex items-center gap-3 bg-blue-950/40 p-3 rounded-lg border border-blue-900/50">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <div className="flex-1 h-2 bg-slate-700 rounded"></div>
                  <span className="text-[10px] font-bold text-blue-400 uppercase">Digest</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
