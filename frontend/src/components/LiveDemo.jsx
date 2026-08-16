import React, { useState } from 'react';
import { Send, Loader2, RefreshCw, Inbox } from 'lucide-react';

export default function LiveDemo() {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const examples = [
    { label: "Urgent", text: "The production server is down. Customers are unable to access the application. Please investigate immediately." },
    { label: "Important", text: "Your interview has been scheduled for tomorrow at 10:00 AM. Please confirm your attendance." },
    { label: "Digest", text: "Good morning, how are you?" },
    { label: "Ignore", text: "Congratulations! You have won a free vacation. Click here to claim your prize." },
  ];

  const handleAnalyze = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    setResult(null);
    setError(null);
    
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL || '';
      const apiKey = import.meta.env.VITE_API_KEY || 'your_secure_api_key_here';
      const uniqueId = `web_demo_${Date.now()}`;
      
      const payload = {
        message_id: uniqueId,
        user_id: "u_001",
        conversation_type: "personal",
        sender_user_id: "u_002",
        created_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
        message_text: message,
        media_type: "none",
        forwarded_count: 0
      };

      const response = await fetch(`${apiUrl}/api/v1/messages/route`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("SmartInbox backend is currently unavailable. Please make sure Docker services are running.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section id="demo" className="py-24 bg-slate-950 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-900/10 blur-[100px] rounded-full pointer-events-none"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">Try SmartInbox</h2>
          <p className="text-lg text-slate-400">
            Send a message to the real SmartInbox AI routing backend.
          </p>
        </div>

        <div className="max-w-4xl mx-auto flex flex-col md:flex-row gap-8">
          {/* Input side */}
          <div className="w-full md:w-1/2 flex flex-col gap-4">
            <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 focus-within:border-indigo-500/50 transition-colors shadow-2xl">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type a message and let SmartInbox decide what deserves your attention..."
                className="w-full h-48 bg-transparent text-white placeholder-slate-500 p-4 outline-none resize-none"
                disabled={isLoading}
              ></textarea>
              
              <div className="flex justify-between items-center p-2 bg-slate-950/50 rounded-lg border-t border-slate-800">
                <div className="text-xs text-slate-500 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Live Connection
                </div>
                <button 
                  onClick={handleAnalyze} 
                  disabled={isLoading || !message.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-800 disabled:text-slate-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {isLoading ? "Analyzing..." : "Analyze Message"}
                </button>
              </div>
            </div>

            <div>
              <p className="text-sm text-slate-400 mb-3 font-medium">Try an example:</p>
              <div className="flex flex-wrap gap-2">
                {examples.map((ex, i) => (
                  <button 
                    key={i}
                    onClick={() => {
                      setMessage(ex.text);
                      setResult(null);
                      setError(null);
                    }}
                    disabled={isLoading}
                    className="px-3 py-1.5 text-xs font-medium rounded-full bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Result side */}
          <div className="w-full md:w-1/2">
            {error && (
              <div className="h-full flex items-center justify-center p-6 rounded-2xl bg-red-950/20 border border-red-900/50 text-red-400 text-center">
                <p>{error}</p>
              </div>
            )}

            {!result && !error && !isLoading && (
              <div className="h-full flex flex-col items-center justify-center p-12 rounded-2xl border border-dashed border-slate-800 text-slate-600 text-center bg-slate-900/20">
                <Inbox className="w-12 h-12 mb-4 opacity-50" />
                <p>Waiting for a message to analyze...</p>
              </div>
            )}

            {isLoading && (
              <div className="h-full flex flex-col items-center justify-center p-12 rounded-2xl border border-slate-800 bg-slate-900/50">
                <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
                <p className="text-slate-400 animate-pulse">SmartInbox AI is thinking...</p>
              </div>
            )}

            {result && !isLoading && (
              <ResultCard result={result} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function ResultCard({ result }) {
  const getStyles = (action) => {
    switch (action?.toLowerCase()) {
      case 'urgent': return "bg-red-950/30 border-red-900/50 text-red-400 ring-red-500/20";
      case 'important': return "bg-orange-950/30 border-orange-900/50 text-orange-400 ring-orange-500/20";
      case 'digest': return "bg-blue-950/30 border-blue-900/50 text-blue-400 ring-blue-500/20";
      default: return "bg-slate-800/50 border-slate-700 text-slate-400 ring-slate-500/20";
    }
  };

  const getConfidenceColor = (action) => {
    switch (action?.toLowerCase()) {
      case 'urgent': return "text-red-400";
      case 'important': return "text-orange-400";
      case 'digest': return "text-blue-400";
      default: return "text-slate-400";
    }
  };

  const styles = getStyles(result.action);
  const confColor = getConfidenceColor(result.action);
  const confidencePercent = Math.round((result.confidence || 0) * 100);

  return (
    <div className={`h-full flex flex-col p-6 rounded-2xl border shadow-[0_0_30px_inset] ${styles.split(' ')[0]} ${styles.split(' ')[1]} ring-1 ${styles.split(' ')[3]} animate-fade-in`}>
      <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-6">
        SmartInbox Decision
      </div>
      
      <div className="flex items-end justify-between mb-8 pb-6 border-b border-white/10">
        <div>
          <h3 className={`text-4xl md:text-5xl font-black uppercase ${styles.split(' ')[2]}`}>
            {result.action}
          </h3>
          <p className="text-slate-400 text-sm mt-2 font-medium capitalize">
            Type: {result.message_type || 'Unknown'}
          </p>
        </div>
        
        <div className="flex flex-col items-end">
          <div className="text-3xl font-bold text-white flex items-baseline gap-1">
            {confidencePercent}<span className="text-lg text-slate-500">%</span>
          </div>
          <div className={`text-xs font-semibold uppercase ${confColor}`}>
            Confidence
          </div>
        </div>
      </div>
      
      <div className="mb-6">
        <div className="text-xs font-semibold uppercase text-slate-500 mb-2">Reasoning</div>
        <p className="text-slate-300 text-lg leading-relaxed">
          {result.reason}
        </p>
      </div>

      <div className="mt-auto pt-4 bg-black/20 p-4 rounded-xl border border-white/5">
        <div className="text-xs font-semibold uppercase text-slate-500 mb-2">Related Evidence</div>
        <p className="text-sm text-slate-400 font-mono break-all">
          {result.evidence_message_ids === 'none' ? 'No evidence required.' : result.evidence_message_ids}
        </p>
      </div>
    </div>
  );
}
