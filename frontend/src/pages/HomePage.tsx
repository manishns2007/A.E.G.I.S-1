import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, Zap, Eye, GitBranch, FileText, Database,
  Cpu, Play, ArrowRight, Activity, Server, Lock,
  FileCheck, Sparkles, CheckCircle2, Radio, Layers
} from 'lucide-react';
import { motion } from 'framer-motion';
import { getSystemHealth } from '../services/api';

const AGENT_SWARM = [
  {
    id: 'orchestrator',
    name: 'Investigation Orchestrator',
    type: 'Meta-Planner',
    icon: Cpu,
    color: 'border-cyan-500/40 text-cyan-400 bg-cyan-500/5',
    badge: 'LangGraph Engine',
    description: 'Autonomously plans step-by-step investigation goals, evaluates evidence uncertainty, and dispatches specialist agents.'
  },
  {
    id: 'intake',
    name: 'Evidence Intake Agent',
    type: 'Custody Chain',
    icon: Database,
    color: 'border-blue-500/40 text-blue-400 bg-blue-500/5',
    badge: 'SHA-256 Custody',
    description: 'Registers evidence packages, calculates SHA-256 cryptographic hashes, extracts EXIF metadata, and inventories files.'
  },
  {
    id: 'privacy',
    name: 'Privacy Shield Agent',
    type: 'Mental Health Guard',
    icon: Shield,
    color: 'border-emerald-500/40 text-emerald-400 bg-emerald-500/5',
    badge: 'YuNet DNN Blur',
    description: 'Instantly redacts human faces and bodies with YuNet DNN & MediaPipe while preserving 100% of background environmental evidence.'
  },
  {
    id: 'enf',
    name: 'ENF Physics Agent',
    type: 'AC Grid Verification',
    icon: Zap,
    color: 'border-amber-500/40 text-amber-400 bg-amber-500/5',
    badge: '50 Hz SciPy FFT',
    description: 'Extracts frame-by-frame luminance oscillations to verify the 50 Hz Indian power grid hum physics, proving authentic capture.'
  },
  {
    id: 'corneal',
    name: 'Corneal Topology Agent',
    type: 'Optical Forensics',
    icon: Eye,
    color: 'border-purple-500/40 text-purple-400 bg-purple-500/5',
    badge: '8 Optical Vectors',
    description: 'Analyzes specular corneal reflections, PRNU camera sensor noise, frequency DCT spectra, and compression artifacts.'
  },
  {
    id: 'vision',
    name: 'Vision Intelligence Agent',
    type: 'VLM Scene Parser',
    icon: Eye,
    color: 'border-pink-500/40 text-pink-400 bg-pink-500/5',
    badge: 'Gemini VLM',
    description: 'Scans background environments to extract furniture, lighting signatures, wall textures, and spatial contextual objects.'
  },
  {
    id: 'graph',
    name: 'Knowledge Graph Agent',
    type: 'Visuo-Acoustic Graph',
    icon: GitBranch,
    color: 'border-indigo-500/40 text-indigo-400 bg-indigo-500/5',
    badge: 'NetworkX Graph',
    description: 'Maps environmental entities into spatial knowledge graphs and performs cross-case correlation matching.'
  },
  {
    id: 'risk',
    name: 'Risk Assessment Agent',
    type: 'Threat Evaluator',
    icon: Activity,
    color: 'border-rose-500/40 text-rose-400 bg-rose-500/5',
    badge: 'Bayesian Fusion',
    description: 'Computes ensemble forensic anomaly scores and determines authentic vs synthetic AI deepfake probability.'
  },
  {
    id: 'gap',
    name: 'Evidence Gap Agent',
    type: 'Uncertainty Resolver',
    icon: Layers,
    color: 'border-yellow-500/40 text-yellow-400 bg-yellow-500/5',
    badge: 'Gap Analysis',
    description: 'Identifies missing forensic vectors and suggests targeted follow-up actions to reach court admissibility.'
  },
  {
    id: 'legal',
    name: 'Legal Reasoning Agent',
    type: 'Statutory Reporter',
    icon: FileText,
    color: 'border-teal-500/40 text-teal-400 bg-teal-500/5',
    badge: 'BSA 2023 Sec 63',
    description: 'Generates plain-English court reports fully compliant with Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023.'
  }
];

const HomePage = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const data = await getSystemHealth();
        if (isMounted) setHealth(data);
      } catch {
        if (isMounted) setHealth(null);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-background text-textMain relative overflow-hidden">
      {/* Dynamic Agentic Background Ambient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-gradient-to-b from-primary/10 via-accent/5 to-transparent blur-3xl pointer-events-none rounded-full" />
      <div className="absolute top-1/3 -left-48 w-96 h-96 bg-primary/5 blur-3xl pointer-events-none rounded-full" />
      <div className="absolute top-1/2 -right-48 w-96 h-96 bg-accent/5 blur-3xl pointer-events-none rounded-full" />

      <div className="max-w-7xl mx-auto px-6 py-12 relative z-10 space-y-16">

        {/* ═══ HERO SECTION ═══ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-6 max-w-4xl mx-auto"
        >
          {/* Live Agentic Status Pill */}
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full border border-primary/30 bg-primary/10 text-primary text-xs font-mono tracking-widest uppercase">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            <span>AUTONOMOUS AGENTIC SWARM ACTIVE</span>
            <span className="text-textMuted">|</span>
            <span className="text-success font-semibold">BSA 2023 SEC 63 COMPLIANT</span>
          </div>

          {/* Hero Title */}
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-textMain leading-tight">
            PROJECT <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-cyan-400 to-accent">A.E.G.I.S.</span>
          </h1>

          <p className="text-lg md:text-xl text-secondary max-w-3xl mx-auto font-light leading-relaxed">
            <strong className="text-textMain font-semibold">Agentic Environmental Graphing &amp; Intelligence System</strong>
            <br />
            Shifting digital forensics away from victim pixel-matching toward analyzing invisible environmental physics, 50 Hz power grid hums, corneal specular topology, and spatial knowledge graphs.
          </p>

          {/* Quick Action CTA Buttons */}
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <motion.button
              whileHover={{ scale: 1.03, boxShadow: '0 0 30px rgba(0,210,255,0.3)' }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/workspace')}
              className="flex items-center space-x-3 px-8 py-4 rounded-xl bg-primary text-background font-bold tracking-wider uppercase text-sm cursor-pointer shadow-lg shadow-primary/20 transition-all"
            >
              <Play className="w-5 h-5 fill-current" />
              <span>Launch Investigation Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/workspace')}
              className="flex items-center space-x-3 px-8 py-4 rounded-xl bg-surface border border-border hover:border-primary/50 text-textMain font-bold tracking-wider uppercase text-sm cursor-pointer transition-all"
            >
              <Database className="w-5 h-5 text-accent" />
              <span>Browse Evidence Locker</span>
            </motion.button>
          </div>
        </motion.div>

        {/* ═══ LIVE SYSTEM TELEMETRY STRIP ═══ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-surface/60 backdrop-blur-md border border-border/80 rounded-2xl p-6 shadow-xl"
        >
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-xs text-textMuted uppercase tracking-wider">
              <Cpu className="w-4 h-4 text-primary" />
              <span>Swarm Orchestrator</span>
            </div>
            <p className="text-xl font-bold font-mono text-success flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              LANGGRAPH ACTIVE
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-xs text-textMuted uppercase tracking-wider">
              <Server className="w-4 h-4 text-accent" />
              <span>Vision LLM Engine</span>
            </div>
            <p className="text-xl font-bold font-mono text-primary uppercase">
              {loading ? 'Checking...' : health?.providers?.gemini === 'online' ? 'Gemini 2.5 Flash' : 'Local Fallback'}
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-xs text-textMuted uppercase tracking-wider">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Privacy Redaction</span>
            </div>
            <p className="text-xl font-bold font-mono text-emerald-400">
              YUNET DNN ACTIVE
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-xs text-textMuted uppercase tracking-wider">
              <FileCheck className="w-4 h-4 text-purple-400" />
              <span>Legal Admissibility</span>
            </div>
            <p className="text-xl font-bold font-mono text-purple-400">
              BSA 2023 SEC 63
            </p>
          </div>
        </motion.div>

        {/* ═══ AGENTIC AI SWARM ARCHITECTURE ═══ */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-textMain tracking-wider uppercase flex items-center gap-3">
                <Sparkles className="w-6 h-6 text-accent" />
                Specialist Agentic Swarm
              </h2>
              <p className="text-secondary text-sm mt-1">
                10 autonomous agents collaborate dynamically to analyze physics, optical topology, and environmental context.
              </p>
            </div>

            <div className="hidden md:flex items-center space-x-2 bg-surface border border-border px-3 py-1.5 rounded-lg text-xs font-mono text-textMuted">
              <Radio className="w-3.5 h-3.5 text-success animate-pulse" />
              <span>AUTONOMOUS WORKFLOW</span>
            </div>
          </div>

          {/* Agent Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {AGENT_SWARM.map((agent, idx) => {
              const Icon = agent.icon;
              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.05 * idx }}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  className={`border rounded-2xl p-5 bg-surface/80 hover:bg-surfaceHover transition-all flex flex-col justify-between group shadow-lg ${agent.color}`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2.5 rounded-xl bg-surface border border-border group-hover:border-primary/50 transition-colors">
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <span className="text-[10px] font-mono uppercase tracking-widest text-textMuted">Agent {idx + 1}</span>
                          <h3 className="text-sm font-bold text-textMain leading-tight">{agent.name}</h3>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border border-current opacity-80">
                        {agent.badge}
                      </span>
                    </div>

                    <p className="text-xs text-secondary leading-relaxed">
                      {agent.description}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-[11px] font-mono text-textMuted">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-success" />
                      <span>{agent.type}</span>
                    </span>
                    <span className="text-primary opacity-0 group-hover:opacity-100 transition-opacity font-bold">
                      ACTIVE &rarr;
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* ═══ BSA 2023 STATUTORY FORENSIC FOOTER ═══ */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="bg-surface border border-border/80 rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-6"
        >
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center space-x-2 text-accent text-xs font-mono font-bold uppercase tracking-widest">
              <Lock className="w-4 h-4" />
              <span>Section 63 BSA 2023 Certificate Generation</span>
            </div>
            <h3 className="text-lg font-bold text-textMain">Ready to run an autonomous investigation?</h3>
            <p className="text-xs text-secondary leading-relaxed">
              Upload any evidence file or select an existing case from the Evidence Locker. A.E.G.I.S. executes all 10 specialist agents in parallel, generating court-admissible forensic legal certificates in seconds.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/workspace')}
            className="flex items-center space-x-3 px-6 py-3.5 rounded-xl bg-accent text-background font-bold tracking-wider uppercase text-xs cursor-pointer shadow-lg shadow-accent/20 flex-shrink-0"
          >
            <span>Enter Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </motion.button>
        </motion.div>

      </div>
    </div>
  );
};

export default HomePage;
