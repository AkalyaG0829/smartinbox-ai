import React from 'react';
import { Inbox } from 'lucide-react';
import { NavLink, Link } from 'react-router-dom';

export default function Navigation() {
  const getNavClass = ({ isActive }) =>
    `transition-colors ${isActive ? 'text-white' : 'hover:text-white'}`;

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="bg-indigo-600 p-1.5 rounded-lg">
            <Inbox className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg leading-tight tracking-tight text-white">SmartInbox</span>
            <span className="text-[10px] text-indigo-400 font-medium tracking-wider uppercase leading-none">AI-Powered Message Intelligence</span>
          </div>
        </Link>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <NavLink to="/" className={getNavClass} end>Home</NavLink>
          <NavLink to="/live-demo" className={getNavClass}>Live Demo</NavLink>
          <NavLink to="/how-it-works" className={getNavClass}>How It Works</NavLink>
          <NavLink to="/architecture" className={getNavClass}>Architecture</NavLink>
          <NavLink to="/observability" className={getNavClass}>Observability</NavLink>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-slow"></div>
            <span className="text-slate-400">AI Engine Online</span>
          </div>
          <Link to="/live-demo" className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors shadow-[0_0_15px_rgba(79,70,229,0.3)]">
            Try Live Demo
          </Link>
        </div>
      </div>
    </nav>
  );
}
