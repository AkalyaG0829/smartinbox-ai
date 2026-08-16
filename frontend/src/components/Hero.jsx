import React from 'react';
import { ArrowRight, BrainCircuit, Inbox, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import RoutingVisualization from './RoutingVisualization';

export default function Hero() {

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
          <Link to="/live-demo" className="w-full sm:w-auto flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-8 py-3.5 rounded-xl transition-all shadow-lg hover:shadow-indigo-600/25">
            Try Live Demo
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/architecture" className="w-full sm:w-auto flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white font-medium px-8 py-3.5 rounded-xl transition-all border border-slate-700">
            View Architecture
          </Link>
        </div>

        {/* Visual Illustration */}
        <RoutingVisualization />
      </div>
    </section>
  );
}
