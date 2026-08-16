import React from 'react';
import { AlertCircle, AlertTriangle, Info, Trash2 } from 'lucide-react';

export default function Categories() {
  const categories = [
    {
      title: "URGENT",
      icon: AlertCircle,
      color: "red",
      desc: "Requires immediate attention.",
      example: "Production server is down. Please investigate immediately."
    },
    {
      title: "IMPORTANT",
      icon: AlertTriangle,
      color: "orange",
      desc: "Important information that should be handled soon.",
      example: "Your interview is scheduled for tomorrow at 10 AM."
    },
    {
      title: "DIGEST",
      icon: Info,
      color: "blue",
      desc: "Useful information that can be reviewed later.",
      example: "Good morning, how are you?"
    },
    {
      title: "IGNORE",
      icon: Trash2,
      color: "slate",
      desc: "Low-value or unwanted information that does not require attention.",
      example: "You've won a FREE iPhone! Click here!"
    }
  ];

  const colorStyles = {
    red: "bg-red-950/20 border-red-900/30 text-red-400",
    orange: "bg-orange-950/20 border-orange-900/30 text-orange-400",
    blue: "bg-blue-950/20 border-blue-900/30 text-blue-400",
    slate: "bg-slate-800/30 border-slate-700 text-slate-400"
  };

  const iconStyles = {
    red: "text-red-500 bg-red-500/10",
    orange: "text-orange-500 bg-orange-500/10",
    blue: "text-blue-500 bg-blue-500/10",
    slate: "text-slate-400 bg-slate-700/30"
  };

  return (
    <section className="py-24 bg-slate-950">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Routing Categories</h2>
          <p className="text-slate-400">
            SmartInbox classifies incoming messages into four standardized priority levels based on AI context analysis.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {categories.map((cat, idx) => (
            <div key={idx} className={`p-6 rounded-2xl border ${colorStyles[cat.color]} backdrop-blur-sm flex flex-col h-full`}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg ${iconStyles[cat.color]}`}>
                  <cat.icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold tracking-wide">{cat.title}</h3>
              </div>
              
              <p className="text-sm text-slate-300 mb-6 flex-grow">{cat.desc}</p>
              
              <div className="mt-auto">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mb-2">Example</div>
                <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 text-sm text-slate-400 italic">
                  "{cat.example}"
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
