import React, { useState, useEffect } from 'react';
import { BrainCircuit, BellRing, Inbox, BookOpen, Ban, ShieldCheck, Activity, Search } from 'lucide-react';

const messages = [
  {
    id: 1,
    text: "Your father had a heart attack. You need to be here as soon as possible.",
    sender: "Family Emergency",
    type: "URGENT",
    action: "NOTIFY",
    destLabel: "Notify immediately",
    confidence: "98%",
    signals: ["Semantic match", "Urgency: High", "Context: Personal"],
    color: "red",
    icon: BellRing
  },
  {
    id: 2,
    text: "Your interview is scheduled for tomorrow at 10:00 AM. Please confirm your attendance.",
    sender: "HR Department",
    type: "IMPORTANT",
    action: "PRIORITIZE",
    destLabel: "Priority inbox",
    confidence: "92%",
    signals: ["Semantic match", "Context: Work", "Time-sensitive"],
    color: "orange",
    icon: Inbox
  },
  {
    id: 3,
    text: "Here is this week's company newsletter and product updates.",
    sender: "Internal Comms",
    type: "DIGEST",
    action: "DIGEST",
    destLabel: "Read later",
    confidence: "88%",
    signals: ["Semantic match", "Context: General", "Low Urgency"],
    color: "blue",
    icon: BookOpen
  },
  {
    id: 4,
    text: "Congratulations! You won a ₹10,000 cash prize. Click here to claim.",
    sender: "Unknown Sender",
    type: "IGNORE",
    action: "IGNORE",
    destLabel: "Automatically filtered",
    confidence: "97%",
    signals: ["Spam signal detected", "Promotional", "Urgency: Fake"],
    color: "slate",
    icon: Ban
  }
];

export default function RoutingVisualization() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [phase, setPhase] = useState('incoming'); // incoming -> analyzing -> routed
  
  useEffect(() => {
    let timer;
    if (phase === 'incoming') {
      timer = setTimeout(() => setPhase('analyzing'), 1500);
    } else if (phase === 'analyzing') {
      timer = setTimeout(() => setPhase('routed'), 2000);
    } else if (phase === 'routed') {
      timer = setTimeout(() => {
        setPhase('incoming');
        setCurrentIndex((prev) => (prev + 1) % messages.length);
      }, 3000);
    }
    return () => clearTimeout(timer);
  }, [phase]);

  const msg = messages[currentIndex];

  const getColorClasses = (color) => {
    switch (color) {
      case 'red': return { border: 'border-red-500/50', bg: 'bg-red-950/40', text: 'text-red-400', glow: 'shadow-[0_0_15px_rgba(239,68,68,0.3)]' };
      case 'orange': return { border: 'border-orange-500/50', bg: 'bg-orange-950/40', text: 'text-orange-400', glow: 'shadow-[0_0_15px_rgba(249,115,22,0.3)]' };
      case 'blue': return { border: 'border-blue-500/50', bg: 'bg-blue-950/40', text: 'text-blue-400', glow: 'shadow-[0_0_15px_rgba(59,130,246,0.3)]' };
      default: return { border: 'border-slate-500/50', bg: 'bg-slate-800/60', text: 'text-slate-400', glow: 'shadow-[0_0_15px_rgba(148,163,184,0.3)]' };
    }
  };

  const colors = getColorClasses(msg.color);
  const Icon = msg.icon;

  return (
    <div className="w-full max-w-5xl mx-auto mt-12 mb-8">
      
      {/* Header / Meta */}
      <div className="flex flex-col sm:flex-row items-center justify-between mb-6 px-4 gap-4">
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-700/50 px-4 py-2 rounded-full backdrop-blur-md">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </div>
          <span className="text-sm font-semibold tracking-widest uppercase text-emerald-400">AI Routing Engine • Live</span>
        </div>
        
        <div className="flex items-center gap-6 text-sm text-slate-400 bg-slate-900/50 border border-slate-800 px-4 py-2 rounded-full">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>1,284 messages analyzed</span>
          </div>
          <div className="w-px h-4 bg-slate-700"></div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>98.4% routing confidence</span>
          </div>
        </div>
      </div>

      {/* Main Visualization Container */}
      <div className="relative rounded-2xl border border-slate-800 bg-slate-950/80 p-8 backdrop-blur-xl shadow-2xl overflow-hidden min-h-[400px] flex items-center">
        
        {/* Animated grid background */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'linear-gradient(to right, #4f46e5 1px, transparent 1px), linear-gradient(to bottom, #4f46e5 1px, transparent 1px)', backgroundSize: '40px 40px' }}></div>
        
        <div className="flex w-full items-center justify-between relative z-10 h-full gap-4">
          
          {/* 1. INCOMING */}
          <div className="w-1/3 flex flex-col items-center">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Incoming Message</div>
            
            <div className={`w-full max-w-[280px] p-5 rounded-xl border transition-all duration-500 ${phase === 'incoming' ? 'bg-slate-800 border-indigo-500/50 shadow-[0_0_20px_rgba(99,102,241,0.2)] scale-105' : 'bg-slate-800/50 border-slate-700 opacity-60 scale-95'}`}>
              <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-700">
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-white">
                  {msg.sender.charAt(0)}
                </div>
                <div className="text-sm font-medium text-slate-300 truncate">{msg.sender}</div>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed">"{msg.text}"</p>
            </div>
          </div>

          {/* 2. AI ENGINE */}
          <div className="w-1/3 flex flex-col items-center justify-center relative">
            <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-slate-800 via-indigo-500 to-slate-800 -z-10 -translate-y-1/2 opacity-50"></div>
            
            <div className={`relative w-24 h-24 flex items-center justify-center rounded-2xl border transition-all duration-500 z-10 ${phase === 'analyzing' ? 'bg-indigo-600 border-indigo-400 shadow-[0_0_30px_rgba(79,70,229,0.5)] scale-110' : 'bg-slate-900 border-slate-700 shadow-lg scale-100'}`}>
              {phase === 'analyzing' && <div className="absolute inset-0 rounded-2xl bg-indigo-500 animate-ping opacity-20"></div>}
              <BrainCircuit className={`w-10 h-10 ${phase === 'analyzing' ? 'text-white' : 'text-indigo-400'}`} />
            </div>

            <div className="h-28 mt-6 w-full flex justify-center">
              {phase === 'analyzing' && (
                <div className="flex flex-col items-center animate-fade-in-up w-full">
                  <div className="text-indigo-400 font-bold text-sm tracking-widest uppercase mb-3 flex items-center gap-2">
                    <Search className="w-4 h-4 animate-spin-slow" />
                    Analyzing...
                  </div>
                  <div className="flex flex-col gap-1.5 w-full items-center">
                    {msg.signals.map((signal, i) => (
                      <div key={i} className="text-xs bg-indigo-950/50 border border-indigo-900/50 text-indigo-300 px-3 py-1 rounded-md text-center shadow-sm w-max" style={{ animationDelay: `${i * 150}ms` }}>
                        {signal}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 3. ROUTED */}
          <div className="w-1/3 flex flex-col items-center">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Routing Decision</div>
            
            <div className={`w-full max-w-[280px] p-5 rounded-xl border transition-all duration-500 ${phase === 'routed' ? `${colors.bg} ${colors.border} ${colors.glow} scale-105 opacity-100` : 'bg-slate-900/50 border-slate-800 opacity-30 scale-95'}`}>
              <div className="flex items-center justify-between mb-4">
                <div className={`flex items-center gap-2 font-black text-lg ${colors.text}`}>
                  <Icon className="w-5 h-5" />
                  {msg.action}
                </div>
                <div className="text-xs font-bold bg-slate-900/50 px-2 py-1 rounded-md text-slate-300 border border-slate-700">
                  {msg.confidence}
                </div>
              </div>
              <div className="text-sm font-medium text-slate-300 border-t border-white/10 pt-3">
                {msg.destLabel}
              </div>
            </div>
          </div>
          
        </div>
      </div>
      
      {/* Inline styles for custom animations */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.4s ease-out forwards;
        }
        @keyframes spinSlow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spinSlow 3s linear infinite;
        }
      `}} />
    </div>
  );
}
