import React from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import Navigation from './components/Navigation';
import Home from './pages/Home';
import LiveDemo from './components/LiveDemo';
import HowItWorks from './components/HowItWorks';
import Architecture from './components/Architecture';
import Observability from './components/Observability';
import SystemHealth from './components/SystemHealth';
import Footer from './components/Footer';

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();
  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function App() {
  return (
    <HashRouter>
      <div className="min-h-screen bg-slate-950 text-slate-50 selection:bg-indigo-500/30 flex flex-col">
        <SystemHealth />
        <Navigation />
        <ScrollToTop />
        <main className="flex-grow flex flex-col relative">
          <Routes>
            <Route path="/" element={<div className="animate-fade-in"><Home /></div>} />
            <Route path="/live-demo" element={<div className="animate-fade-in"><div className="pt-8"><LiveDemo /></div></div>} />
            <Route path="/how-it-works" element={<div className="animate-fade-in"><HowItWorks /></div>} />
            <Route path="/architecture" element={<div className="animate-fade-in"><Architecture /></div>} />
            <Route path="/observability" element={<div className="animate-fade-in"><Observability /></div>} />
          </Routes>
        </main>
        <Footer />
      </div>
    </HashRouter>
  );
}

export default App;
