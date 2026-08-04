import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Shield, Server, Activity, Database, Cpu } from 'lucide-react';
import Workspace from './pages/Workspace';
import Investigation from './pages/Investigation';
import Results from './pages/Results';
import Report from './pages/Report';

const TopNav = () => (
  <header className="bg-surface border-b border-border px-6 py-4 flex items-center justify-between">
    <div className="flex items-center space-x-3">
      <Shield className="text-primary w-8 h-8" />
      <div>
        <h1 className="text-xl font-bold tracking-wider text-textMain m-0 leading-tight">PROJECT A.E.G.I.S.</h1>
        <p className="text-xs text-textMuted uppercase tracking-widest mt-0.5">Agentic Environmental Graphing &amp; Intelligence System</p>
      </div>
    </div>

    <div className="flex items-center space-x-6 text-xs">
      <div className="flex items-center space-x-2">
        <Cpu className="w-3.5 h-3.5 text-textMuted" />
        <span className="text-textMuted uppercase tracking-wide">Orchestrator:</span>
        <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
        <span className="text-success font-semibold uppercase">Online</span>
      </div>
      <div className="flex items-center space-x-2">
        <Server className="w-3.5 h-3.5 text-textMuted" />
        <span className="text-textMuted uppercase tracking-wide">Forensic Pipeline:</span>
        <span className="text-success font-semibold uppercase">Ready</span>
      </div>
      <div className="flex items-center space-x-2">
        <Activity className="w-3.5 h-3.5 text-textMuted" />
        <span className="text-textMuted uppercase tracking-wide">Vision Intelligence:</span>
        <span className="text-primary font-semibold uppercase">Standby</span>
      </div>
      <div className="flex items-center space-x-2">
        <Database className="w-3.5 h-3.5 text-textMuted" />
        <span className="text-textMuted uppercase tracking-wide">Evidence Locker:</span>
        <span className="text-success font-semibold uppercase">Connected</span>
      </div>
    </div>
  </header>
);

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <TopNav />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/investigation" element={<Investigation />} />
            {/* Legacy route kept for backwards compat */}
            <Route path="/processing/:caseId" element={<Investigation />} />
            <Route path="/results/:caseId" element={<Results />} />
            <Route path="/report/:caseId" element={<Report />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
