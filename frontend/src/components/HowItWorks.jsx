import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, BrainCircuit, Activity, CheckCircle2, AlertTriangle, 
  BellRing, Inbox, BookOpen, Ban, ArrowRight, ShieldCheck, Mail
} from 'lucide-react';

const scenarios = [
  {
    id: 1,
    sender: "Mom",
    time: "Just now",
    message: "Your father has been admitted to the hospital. Please come immediately.",
    intent: "Emergency",
    context: "Family / Medical",
    urgency: "Very High",
    confidence: "96%",
    decision: "NOTIFY",
    reason: "Time-sensitive medical emergency requiring immediate attention.",
    actions: ["Push notification", "High-priority alert", "Appears at top of inbox"],
    color: "red",
    icon: BellRing
  },
  {
    id: 2,
    sender: "HR Dept",
    time: "2 mins ago",
    message: "Your job interview has been scheduled for tomorrow at 10 AM. Please confirm your attendance.",
    intent: "Meeting/Interview",
    context: "Professional",
    urgency: "Medium-High",
    confidence: "91%",
    decision: "IMPORTANT",
    reason: "Time-sensitive work event requiring user confirmation.",
    actions: ["Silent notification", "Priority inbox placement", "Calendar suggestion"],
    color: "orange",
    icon: Inbox
  },
  {
    id: 3,
    sender: "Internal Comms",
    time: "1 hour ago",
    message: "Here is this week's company newsletter with product updates and announcements.",
    intent: "Information",
    context: "Company News",
    urgency: "Low",
    confidence: "84%",
    decision: "DIGEST",
    reason: "General non-urgent reading material suitable for batch processing.",
    actions: ["No notification", "Grouped in daily digest", "Marked as read/skim"],
    color: "blue",
    icon: BookOpen
  },
  {
    id: 4,
    sender: "Unknown",
    time: "3 hours ago",
    message: "Congratulations! You won ₹10,000. Click here to claim your prize.",
    intent: "Scam/Phishing",
    context: "Promotional",
    urgency: "Fake",
    confidence: "98%",
    decision: "IGNORE",
    reason: "Strong promotional and scam indicators detected.",
    actions: ["Silently filtered", "Moved to junk", "Sender reputation penalized"],
    color: "slate",
    icon: Ban
  }
];

export default function HowItWorks() {
  const [currentScenario, setCurrentScenario] = useState(0);
  const [phase, setPhase] = useState(0); 
  // Phases: 
  // 0: Message appears
  // 1: AI scans/analyzes
  // 2: Analysis values appear
  // 3: Decision generated & Action

  useEffect(() => {
    let timer;
    if (phase === 0) {
      timer = setTimeout(() => setPhase(1), 1500);
    } else if (phase === 1) {
      timer = setTimeout(() => setPhase(2), 2000);
    } else if (phase === 2) {
      timer = setTimeout(() => setPhase(3), 2000);
    } else if (phase === 3) {
      timer = setTimeout(() => {
        setPhase(0);
        setCurrentScenario((prev) => (prev + 1) % scenarios.length);
      }, 4000);
    }
    return () => clearTimeout(timer);
  }, [phase]);

  const scenario = scenarios[currentScenario];
  const Icon = scenario.icon;

  const getColorTheme = (color) => {
    switch (color) {
      case 'red': return { border: 'border-red-500/50', bg: 'bg-red-950/40', text: 'text-red-400', glow: 'shadow-[0_0_20px_rgba(239,68,68,0.3)]', badge: 'bg-red-500/20 text-red-300' };
      case 'orange': return { border: 'border-orange-500/50', bg: 'bg-orange-950/40', text: 'text-orange-400', glow: 'shadow-[0_0_20px_rgba(249,115,22,0.3)]', badge: 'bg-orange-500/20 text-orange-300' };
      case 'blue': return { border: 'border-blue-500/50', bg: 'bg-blue-950/40', text: 'text-blue-400', glow: 'shadow-[0_0_20px_rgba(59,130,246,0.3)]', badge: 'bg-blue-500/20 text-blue-300' };
      default: return { border: 'border-slate-500/50', bg: 'bg-slate-800/60', text: 'text-slate-400', glow: 'shadow-[0_0_20px_rgba(148,163,184,0.3)]', badge: 'bg-slate-600/30 text-slate-300' };
    }
  };

  const theme = getColorTheme(scenario.color);

  return (
    <section id="how-it-works" className="py-24 bg-slate-900 border-y border-slate-800 relative overflow-hidden">
      
      {/* Background elements */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-900/10 blur-[100px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-slate-800/20 blur-[120px] rounded-full pointer-events-none"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">How SmartInbox Works</h2>
          <p className="text-lg text-slate-400">
            SmartInbox doesn't just read words—it understands context, determines priority, and takes the right action.
          </p>
        </div>

        {/* Workflow Container */}
        <div className="max-w-6xl mx-auto rounded-3xl border border-slate-800 bg-slate-950/60 p-4 md:p-8 lg:p-12 backdrop-blur-xl shadow-2xl">
          
          <div className="flex flex-col lg:flex-row gap-8 lg:gap-12 items-stretch justify-between">
            
            {/* COLUMN 1: Incoming Message */}
            <div className="flex-1 flex flex-col items-center">
              <div className="w-full flex items-center justify-center gap-2 text-sm font-semibold text-slate-400 uppercase tracking-widest mb-6">
                <Mail className="w-4 h-4" />
                <span>Incoming</span>
              </div>
              
              <div className={`w-full bg-slate-900 rounded-2xl border transition-all duration-700 p-6 ${phase >= 0 ? 'border-slate-700 shadow-lg scale-100 opacity-100' : 'border-slate-800 opacity-0 scale-95'}`}>
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-indigo-900/50 flex items-center justify-center border border-indigo-700/50 text-indigo-300 font-bold">
                      {scenario.sender.charAt(0)}
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">{scenario.sender}</div>
                      <div className="text-xs text-slate-500">{scenario.time}</div>
                    </div>
                  </div>
                </div>
                <div className="text-slate-300 leading-relaxed font-medium">
                  "{scenario.message}"
                </div>
              </div>
            </div>

            {/* CONNECTION 1 */}
            <div className="hidden lg:flex flex-col justify-center items-center px-2">
              <ArrowRight className={`w-6 h-6 transition-colors duration-500 ${phase >= 1 ? 'text-indigo-400' : 'text-slate-700'}`} />
            </div>

            {/* COLUMN 2: AI Processing & Analysis */}
            <div className="flex-1 flex flex-col items-center">
              <div className="w-full flex items-center justify-center gap-2 text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-6">
                <BrainCircuit className="w-4 h-4" />
                <span>SmartInbox AI</span>
              </div>
              
              <div className={`w-full bg-slate-900 rounded-2xl border transition-all duration-700 p-6 flex flex-col h-full ${phase >= 1 ? 'border-indigo-500/50 shadow-[0_0_30px_rgba(99,102,241,0.15)]' : 'border-slate-800 opacity-40'}`}>
                
                <div className="flex items-center justify-center mb-6 relative">
                  {phase === 1 && <div className="absolute inset-0 bg-indigo-500 rounded-full blur-xl opacity-20 animate-pulse"></div>}
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center border transition-all duration-500 z-10 ${phase === 1 ? 'bg-indigo-600 border-indigo-400 shadow-[0_0_20px_rgba(79,70,229,0.5)] scale-110' : 'bg-slate-800 border-slate-700'}`}>
                    <BrainCircuit className={`w-8 h-8 ${phase === 1 ? 'text-white animate-pulse' : 'text-indigo-500'}`} />
                  </div>
                </div>

                {/* Analysis Steps or Values */}
                <div className="flex-1 flex flex-col justify-center min-h-[140px]">
                  {phase === 1 ? (
                    <div className="space-y-3 animate-fade-in">
                      <div className="flex items-center gap-3 text-sm text-indigo-300">
                        <Activity className="w-4 h-4 animate-spin-slow" /> Reading message...
                      </div>
                      <div className="flex items-center gap-3 text-sm text-indigo-300/80">
                        <Activity className="w-4 h-4 animate-spin-slow animation-delay-1" /> Understanding context...
                      </div>
                      <div className="flex items-center gap-3 text-sm text-indigo-300/60">
                        <Activity className="w-4 h-4 animate-spin-slow animation-delay-2" /> Detecting urgency...
                      </div>
                    </div>
                  ) : phase >= 2 ? (
                    <div className="space-y-3 animate-fade-in bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                      <div className="text-xs font-bold text-slate-500 uppercase mb-2">Message Analysis</div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-slate-400">Intent:</span>
                        <span className="text-slate-200 font-medium">{scenario.intent}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-slate-400">Context:</span>
                        <span className="text-slate-200 font-medium">{scenario.context}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-slate-400">Urgency:</span>
                        <span className="text-slate-200 font-medium">{scenario.urgency}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm pt-2 border-t border-slate-800 mt-2">
                        <span className="text-slate-400">Confidence:</span>
                        <span className="text-emerald-400 font-bold flex items-center gap-1">
                          <ShieldCheck className="w-4 h-4" /> {scenario.confidence}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-600 text-sm italic">
                      Waiting for message...
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* CONNECTION 2 */}
            <div className="hidden lg:flex flex-col justify-center items-center px-2">
              <ArrowRight className={`w-6 h-6 transition-colors duration-500 ${phase >= 3 ? theme.text : 'text-slate-700'}`} />
            </div>

            {/* COLUMN 3: Decision & Action */}
            <div className="flex-1 flex flex-col items-center">
              <div className="w-full flex items-center justify-center gap-2 text-sm font-semibold text-slate-400 uppercase tracking-widest mb-6">
                <CheckCircle2 className="w-4 h-4" />
                <span>AI Decision & Action</span>
              </div>
              
              <div className={`w-full bg-slate-900 rounded-2xl border transition-all duration-700 flex flex-col h-full ${phase >= 3 ? `${theme.border} ${theme.glow} opacity-100 scale-100` : 'border-slate-800 opacity-30 scale-95'}`}>
                
                {phase >= 3 ? (
                  <div className="p-6 h-full flex flex-col animate-fade-in">
                    
                    <div className="flex items-center justify-between mb-6">
                      <div className={`flex items-center gap-2 font-black text-2xl tracking-wide ${theme.text}`}>
                        <Icon className="w-6 h-6" />
                        {scenario.decision}
                      </div>
                      <div className={`text-xs font-bold px-2 py-1 rounded-md ${theme.badge} border ${theme.border}`}>
                        {scenario.confidence}
                      </div>
                    </div>

                    <div className="mb-6">
                      <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Reasoning</div>
                      <p className="text-slate-300 text-sm leading-relaxed italic">
                        "{scenario.reason}"
                      </p>
                    </div>

                    <div className="mt-auto pt-4 border-t border-slate-800">
                      <div className="text-[10px] font-bold text-slate-500 uppercase mb-3">SmartInbox Action Taken</div>
                      <ul className="space-y-2">
                        {scenario.actions.map((action, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                            <CheckCircle2 className={`w-4 h-4 mt-0.5 ${theme.text}`} />
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                  </div>
                ) : (
                  <div className="p-6 h-full flex items-center justify-center text-slate-600 text-sm italic">
                    Awaiting analysis...
                  </div>
                )}
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
        .animate-fade-in {
          animation: fadeInUp 0.4s ease-out forwards;
        }
        @keyframes spinSlow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spinSlow 3s linear infinite;
        }
        .animation-delay-1 {
          animation-delay: 0.5s;
        }
        .animation-delay-2 {
          animation-delay: 1s;
        }
      `}} />
    </section>
  );
}
