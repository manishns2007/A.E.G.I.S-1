import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, Zap, Eye, GitBranch, FileText, Database,
  Cpu, ArrowRight, Activity, Server, Lock, Layers, CheckCircle2, Sparkles, Radio
} from 'lucide-react';
import { motion } from 'framer-motion';
import { getSystemHealth } from '../services/api';

const FEATURES = [
  {
    icon: Shield,
    title: 'Automated Privacy Shield',
    description: 'Protects investigator mental health by instantly blurring human face and body regions using YuNet DNN & MediaPipe while preserving environmental background.'
  },
  {
    icon: Zap,
    title: 'ENF Physics Engine',
    description: 'Extracts 50 Hz power grid hum luminance oscillations via SciPy STFT & FFT to verify authentic real-world capture vs AI deepfakes.'
  },
  {
    icon: Eye,
    title: 'Multi-Signal Optical Forensics',
    description: 'Ensemble analysis of specular corneal reflections, PRNU camera sensor noise, frequency DCT spectra, and compression artifacts.'
  },
  {
    icon: GitBranch,
    title: 'Visuo-Acoustic Knowledge Graph',
    description: 'Extracts environmental fixtures, furniture, and lighting signatures into spatial graphs using NetworkX and cross-case intelligence correlations.'
  },
  {
    icon: Cpu,
    title: 'Multi-Agent Swarm Planning',
    description: '10 specialist agents collaborate dynamically under a LangGraph meta-orchestrator to formulate hypotheses and fill evidence gaps.'
  },
  {
    icon: FileText,
    title: 'BSA 2023 Section 63 Certificate',
    description: 'Generates plain-English court reports fully compliant with Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023.'
  }
];

const ARCHITECTURE_STEPS = [
  { step: '01', title: 'Evidence Ingestion & Hashing', desc: 'SHA-256 custody chain verification and multi-format evidence extraction.' },
  { step: '02', title: 'Mental Health Privacy Redaction', desc: 'YuNet DNN instant face/body blurring preserving scene background.' },
  { step: '03', title: 'Multi-Signal Forensic Extraction', desc: '50 Hz AC grid physics, corneal topology, and PRNU sensor noise scoring.' },
  { step: '04', title: 'VLM Spatial Entity Graphing', desc: 'Environmental object extraction and NetworkX correlation mapping.' },
  { step: '05', title: 'Statutory Court Certificate', desc: 'BSA 2023 Section 63 dynamic legal docket generation.' }
];

const HomePage = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const data = await getSystemHealth();
        if (isMounted) setHealth(data);
      } catch {
        if (isMounted) setHealth(null);
      }
    };
    fetchHealth();
    return () => { isMounted = false; };
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#060913] text-[#f8fafc] font-sans relative overflow-x-hidden">
      
      {/* ── Background Dot Matrix & Radial Glow ── */}
      <div className="absolute inset-0 bg-dot-matrix opacity-40 pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1200px] h-[600px] bg-radial-glow pointer-events-none" />

      {/* ── Top Navbar ── */}
      <nav className="relative z-20 border-b border-[#1e293b]/80 bg-[#060913]/90 backdrop-blur-md px-8 py-4 flex items-center justify-between">
        {/* Brand Logo Badge */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-8 h-8 rounded-md bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
            A
          </div>
          <span className="text-lg font-bold tracking-widest text-white uppercase">AEGIS</span>
        </div>

        {/* Right Navigation Links & Enter Platform Button */}
        <div className="flex items-center space-x-8 text-sm">
          <button
            onClick={() => scrollToSection('features')}
            className="text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            Features
          </button>
          <button
            onClick={() => scrollToSection('architecture')}
            className="text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            Architecture
          </button>
          <button
            onClick={() => navigate('/workspace')}
            className="px-4 py-2 rounded-lg border border-blue-500/40 text-blue-400 hover:bg-blue-500/10 font-semibold transition-all cursor-pointer"
          >
            Enter Platform
          </button>
        </div>
      </nav>

      {/* ── HERO SECTION ── */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pt-24 pb-20 text-center flex flex-col items-center justify-center">
        
        {/* Top Pill Badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-xs font-mono tracking-widest uppercase mb-8 shadow-sm"
        >
          <span>DIGITAL FORENSICS REDEFINED</span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] text-white mb-6"
        >
          AI-Assisted Digital <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-blue-400 to-indigo-400">
            Investigation Platform
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto font-normal leading-relaxed mb-10"
        >
          Transform digital evidence into actionable intelligence through automated analysis, entity extraction, relationship mapping, and timeline reconstruction.
        </motion.p>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-wrap justify-center items-center gap-4"
        >
          <button
            onClick={() => navigate('/workspace')}
            className="flex items-center space-x-2.5 px-7 py-3.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-600/30 cursor-pointer"
          >
            <span>Launch Investigation</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => scrollToSection('features')}
            className="px-7 py-3.5 rounded-lg border border-[#1e293b] bg-[#0e1424] hover:bg-[#172036] text-slate-200 font-semibold text-sm transition-all cursor-pointer"
          >
            Explore Features
          </button>
        </motion.div>
      </section>

      {/* ── FEATURES SECTION ── */}
      <section id="features" className="relative z-10 max-w-6xl mx-auto px-6 py-20 border-t border-[#1e293b]/60">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-mono uppercase tracking-widest text-blue-400">Platform Capabilities</div>
          <h2 className="text-3xl font-extrabold text-white">Autonomous Specialist Intelligence</h2>
          <p className="text-slate-400 text-sm">
            AEGIS coordinates 10 autonomous forensic agents to analyze physics, optical reflections, and spatial knowledge graphs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <motion.div
                key={feat.title}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: idx * 0.05 }}
                className="p-6 rounded-xl border border-[#1e293b] bg-[#0e1424]/80 hover:bg-[#172036]/90 transition-all space-y-4 group"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:border-blue-500/50 transition-colors">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">{feat.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{feat.description}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ── ARCHITECTURE SECTION ── */}
      <section id="architecture" className="relative z-10 max-w-6xl mx-auto px-6 py-20 border-t border-[#1e293b]/60">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-mono uppercase tracking-widest text-blue-400">Workflow &amp; Admissibility</div>
          <h2 className="text-3xl font-extrabold text-white">End-to-End Forensic Architecture</h2>
          <p className="text-slate-400 text-sm">
            From raw evidence ingestion to BSA 2023 Section 63 statutory court certificate generation.
          </p>
        </div>

        <div className="space-y-4 max-w-4xl mx-auto">
          {ARCHITECTURE_STEPS.map((st, idx) => (
            <motion.div
              key={st.step}
              initial={{ opacity: 0, x: -15 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: idx * 0.08 }}
              className="flex items-start space-x-6 p-5 rounded-xl border border-[#1e293b] bg-[#0e1424]/80 hover:bg-[#172036]/90 transition-all"
            >
              <span className="text-xl font-mono font-extrabold text-blue-400 flex-shrink-0">{st.step}</span>
              <div>
                <h4 className="text-base font-bold text-white">{st.title}</h4>
                <p className="text-xs text-slate-400 mt-1">{st.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="relative z-10 border-t border-[#1e293b]/80 bg-[#060913] px-8 py-8 text-center text-xs text-slate-500 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <span className="font-bold text-slate-300">AEGIS Platform</span>
          <span>·</span>
          <span>Agentic Environmental Graphing &amp; Intelligence System</span>
        </div>
        <div>
          <span>Fully compliant with Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023</span>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
