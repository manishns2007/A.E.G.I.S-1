import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Server, Activity, Database, Cpu, Home, FolderKanban, Play } from 'lucide-react';
import HomePage from './pages/HomePage';
import Workspace from './pages/Workspace';
import Investigation from './pages/Investigation';
import Results from './pages/Results';
import Report from './pages/Report';
import { getSystemHealth } from './services/api';

const TopNav = () => {
  const location = useLocation();
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const data = await getSystemHealth();
        if (isMounted) setHealth(data);
      } catch {
        if (isMounted) setHealth(null);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const isGeminiOnline = health?.providers?.gemini === 'online';
  const isGroqOnline = health?.providers?.groq === 'online';

  if (location.pathname === '/') return null;

  return (
    <header className="bg-surface/90 backdrop-blur-md border-b border-border px-6 py-3 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50">
      {/* Brand & Title */}
      <Link to="/" className="flex items-center space-x-3 group">
        <div className="w-8 h-8 rounded-md bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
          A
        </div>
        <div>
          <h1 className="text-lg font-extrabold tracking-wider text-textMain m-0 leading-tight flex items-center gap-2">
            AEGIS
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-primary/20 text-primary uppercase">Agentic AI</span>
          </h1>
          <p className="text-[11px] text-textMuted uppercase tracking-widest mt-0.5">Agentic Environmental Graphing &amp; Intelligence System</p>
        </div>
      </Link>

      {/* Navigation Links */}
      <nav className="flex items-center space-x-2">
        <Link
          to="/"
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            location.pathname === '/'
              ? 'bg-primary/15 text-primary border border-primary/30'
              : 'text-textMuted hover:text-textMain hover:bg-surfaceHover'
          }`}
        >
          <Home className="w-3.5 h-3.5" />
          <span>Home</span>
        </Link>

        <Link
          to="/workspace"
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            location.pathname === '/workspace'
              ? 'bg-primary/15 text-primary border border-primary/30'
              : 'text-textMuted hover:text-textMain hover:bg-surfaceHover'
          }`}
        >
          <FolderKanban className="w-3.5 h-3.5" />
          <span>Workspace</span>
        </Link>

        <Link
          to="/investigation"
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            location.pathname === '/investigation'
              ? 'bg-accent/15 text-accent border border-accent/30'
              : 'text-textMuted hover:text-textMain hover:bg-surfaceHover'
          }`}
        >
          <Play className="w-3.5 h-3.5" />
          <span>Live Investigation</span>
        </Link>
      </nav>

      {/* Dynamic Agent Telemetry Indicators */}
      <div className="hidden lg:flex items-center space-x-5 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <Cpu className="w-3.5 h-3.5 text-primary" />
          <span className="text-textMuted uppercase tracking-wide">Orchestrator:</span>
          <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
          <span className="text-success font-semibold uppercase">LangGraph</span>
        </div>

        <div className="flex items-center space-x-2">
          <Activity className="w-3.5 h-3.5 text-accent" />
          <span className="text-textMuted uppercase tracking-wide">VLM AI:</span>
          <span className={`w-1.5 h-1.5 rounded-full ${isGeminiOnline ? 'bg-success' : 'bg-amber-400'}`} />
          <span className={`font-semibold uppercase ${isGeminiOnline ? 'text-success' : 'text-amber-400'}`}>
            {isGeminiOnline ? 'Gemini VLM' : 'Local Fallback'}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <Server className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-textMuted uppercase tracking-wide">LLM Provider:</span>
          <span className={`font-semibold uppercase ${isGroqOnline ? 'text-purple-400' : 'text-textMuted'}`}>
            {isGroqOnline ? 'Groq Active' : 'Offline'}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <Database className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-textMuted uppercase tracking-wide">BSA Docket:</span>
          <span className="text-emerald-400 font-semibold uppercase">Sec 63 Ready</span>
        </div>
      </div>
    </header>
  );
};

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-background font-sans">
        <TopNav />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/workspace" element={<Workspace />} />
            <Route path="/investigation" element={<Investigation />} />
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
