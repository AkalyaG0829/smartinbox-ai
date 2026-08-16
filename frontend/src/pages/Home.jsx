import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Cpu, Eye, Workflow } from 'lucide-react';
import Hero from '../components/Hero';
import ProblemSolution from '../components/ProblemSolution';
import Categories from '../components/Categories';

export default function Home() {
  return (
    <div className="flex flex-col w-full">
      <Hero />
      <ProblemSolution />
      <Categories />
      
      {/* Quick Previews Section */}
      <section className="py-24 bg-slate-950 border-t border-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">Discover the Technology</h2>
            <p className="text-slate-400">
              SmartInbox is built on a scalable AI pipeline and modern observability stack.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* How It Works Preview */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 flex flex-col items-start transition-all hover:border-slate-700 hover:bg-slate-900">
              <div className="w-12 h-12 rounded-xl bg-indigo-950/50 flex items-center justify-center border border-indigo-900/50 mb-6">
                <Workflow className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">How It Works</h3>
              <p className="text-slate-400 mb-8 flex-grow">
                Explore the complete AI classification pipeline, from semantic analysis to policy engine routing.
              </p>
              <Link to="/how-it-works" className="flex items-center gap-2 text-indigo-400 font-medium hover:text-indigo-300 transition-colors mt-auto">
                Explore How It Works <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Architecture Preview */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 flex flex-col items-start transition-all hover:border-slate-700 hover:bg-slate-900">
              <div className="w-12 h-12 rounded-xl bg-indigo-950/50 flex items-center justify-center border border-indigo-900/50 mb-6">
                <Cpu className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Architecture</h3>
              <p className="text-slate-400 mb-8 flex-grow">
                See how FastAPI, PostgreSQL, Redis, and Celery power our robust backend microservices.
              </p>
              <Link to="/architecture" className="flex items-center gap-2 text-indigo-400 font-medium hover:text-indigo-300 transition-colors mt-auto">
                View Architecture <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Observability Preview */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 flex flex-col items-start transition-all hover:border-slate-700 hover:bg-slate-900">
              <div className="w-12 h-12 rounded-xl bg-indigo-950/50 flex items-center justify-center border border-indigo-900/50 mb-6">
                <Eye className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Observability</h3>
              <p className="text-slate-400 mb-8 flex-grow">
                Monitor system health, classification metrics, and API latency with Prometheus and Grafana.
              </p>
              <Link to="/observability" className="flex items-center gap-2 text-indigo-400 font-medium hover:text-indigo-300 transition-colors mt-auto">
                View Observability <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
