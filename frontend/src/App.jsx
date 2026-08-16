import React from 'react';
import Navigation from './components/Navigation';
import Hero from './components/Hero';
import ProblemSolution from './components/ProblemSolution';
import LiveDemo from './components/LiveDemo';
import Categories from './components/Categories';
import HowItWorks from './components/HowItWorks';
import Architecture from './components/Architecture';
import Observability from './components/Observability';
import SystemHealth from './components/SystemHealth';
import Footer from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 selection:bg-indigo-500/30">
      <SystemHealth />
      <Navigation />
      <main>
        <Hero />
        <ProblemSolution />
        <LiveDemo />
        <Categories />
        <HowItWorks />
        <Architecture />
        <Observability />
      </main>
      <Footer />
    </div>
  );
}

export default App;
