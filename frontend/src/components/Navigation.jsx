import React from 'react';
import { Inbox, Activity } from 'lucide-react';

export default function Navigation() {
  const scrollToDemo = (e) => {
    e.preventDefault();
    document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-indigo-600 p-1.5 rounded-lg">
            <Inbox className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg leading-tight tracking-tight text-white">SmartInbox</span>
            <span className="text-[10px] text-indigo-400 font-medium tracking-wider uppercase leading-none">AI-Powered Message Intelligence</span>
          </div>
        </div>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#" className="hover:text-white transition-colors">Home</a>
          <a href="#demo" onClick={scrollToDemo} className="hover:text-white transition-colors">Live Demo</a>
          <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
          <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
          <a href="#observability" className="hover:text-white transition-colors">Observability</a>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-slow"></div>
            <span className="text-slate-400">AI Engine Online</span>
          </div>
          <button onClick={scrollToDemo} className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors shadow-[0_0_15px_rgba(79,70,229,0.3)]">
            Try Live Demo
          </button>
        </div>
      </div>
    </nav>
  );
}
