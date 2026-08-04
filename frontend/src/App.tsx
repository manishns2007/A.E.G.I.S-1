import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Link } from 'react-router-dom';
import { Shield, Server, Activity, Database, FileText } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Processing from './pages/Processing';
import Results from './pages/Results';
import Report from './pages/Report';

const TopNav = () => (
  <header className="bg-surface border-b border-border px-6 py-4 flex items-center justify-between">
    <div className="flex items-center space-x-3">
      <Shield className="text-primary w-8 h-8" />
      <div>
        <h1 className="text-xl font-bold tracking-wider text-textMain m-0 leading-tight">PROJECT A.E.G.I.S.</h1>
        <p className="text-xs text-textMuted uppercase tracking-widest mt-0.5">Agentic Environmental Graphing & Intelligence System</p>
      </div>
    </div>
    
    <div className="flex space-x-6 text-sm">
      <div className="flex items-center space-x-2">
        <Server className="w-4 h-4 text-textMuted" />
        <span className="text-textMuted uppercase">Inference Engine:</span>
        <span className="text-success font-semibold">Online</span>
      </div>
      <div className="flex items-center space-x-2">
        <Activity className="w-4 h-4 text-textMuted" />
        <span className="text-textMuted uppercase">Pipeline:</span>
        <span className="text-success font-semibold">Ready</span>
      </div>
      <div className="flex items-center space-x-2">
        <Database className="w-4 h-4 text-textMuted" />
        <span className="text-textMuted uppercase">Gemini:</span>
        <span className="text-primary font-semibold">Standby</span>
      </div>
    </div>
  </header>
);

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <TopNav />
        <main className="flex-1 p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/processing/:caseId" element={<Processing />} />
            <Route path="/results/:caseId" element={<Results />} />
            <Route path="/report/:caseId" element={<Report />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
