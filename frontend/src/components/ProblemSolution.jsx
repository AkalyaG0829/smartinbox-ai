import React from 'react';
import { Mail, ShieldAlert, Sparkles, Filter, Trash2, Clock, CheckCircle2 } from 'lucide-react';

export default function ProblemSolution() {
  return (
    <section className="py-24 bg-slate-950">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Too many messages. Not enough attention.
          </h2>
          <p className="text-lg text-slate-400">
            People receive hundreds of messages, notifications, emails, and updates. Important information can easily get buried under a mountain of noise.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-8 items-center max-w-5xl mx-auto">
          {/* Before */}
          <div className="w-full md:w-1/2 p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <h3 className="text-lg font-semibold text-slate-300 mb-6 flex items-center gap-2">
              <Mail className="w-5 h-5 text-slate-500" />
              Before SmartInbox
            </h3>
            
            <div className="space-y-3">
              {[
                { title: "Meeting reminder", icon: Clock },
                { title: "Newsletter: Top 10 tips", icon: Mail },
                { title: "Production server alert", icon: ShieldAlert },
                { title: "Hey, how are you?", icon: Mail },
                { title: "Limited time offer! 50% off", icon: Sparkles },
                { title: "Payment processed successfully", icon: CheckCircle2 }
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 opacity-70 grayscale">
                  <item.icon className="w-5 h-5 text-slate-400" />
                  <span className="text-sm text-slate-300">{item.title}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 text-center text-sm text-slate-500 font-medium">
              Everything looks equally important
            </div>
          </div>

          {/* Arrow */}
          <div className="hidden md:flex flex-shrink-0 items-center justify-center p-4">
            <Filter className="w-8 h-8 text-indigo-500 opacity-50" />
          </div>

          {/* After */}
          <div className="w-full md:w-1/2 p-6 rounded-2xl bg-slate-900/50 border border-indigo-900/30 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4">
              <Sparkles className="w-6 h-6 text-indigo-400 opacity-50" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-indigo-400" />
              After SmartInbox
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 rounded-xl bg-red-950/20 border border-red-900/30">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <span className="text-sm font-medium text-red-100">URGENT</span>
                </div>
                <span className="text-xs font-bold text-red-500 bg-red-500/10 px-2 py-1 rounded">5</span>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-xl bg-orange-950/20 border border-orange-900/30">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  <span className="text-sm font-medium text-orange-100">IMPORTANT</span>
                </div>
                <span className="text-xs font-bold text-orange-500 bg-orange-500/10 px-2 py-1 rounded">18</span>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-xl bg-blue-950/20 border border-blue-900/30">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span className="text-sm font-medium text-blue-100">DIGEST</span>
                </div>
                <span className="text-xs font-bold text-blue-500 bg-blue-500/10 px-2 py-1 rounded">52</span>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-slate-500"></div>
                  <span className="text-sm font-medium text-slate-300">IGNORE</span>
                </div>
                <span className="text-xs font-bold text-slate-400 bg-slate-700/30 px-2 py-1 rounded">25</span>
              </div>
            </div>
            
            <div className="mt-4 text-center text-sm text-indigo-400 font-medium">
              Information automatically categorized
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
