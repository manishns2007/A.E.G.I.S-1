import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Shield, Zap, Eye, GitBranch, FileText, Cpu,
  CheckCircle2, Loader2, Circle, AlertTriangle, XCircle
} from 'lucide-react';
import { analyzeEvidence, startInvestigation } from '../services/api';

type AgentStatus = 'ready' | 'running' | 'completed' | 'warning' | 'failed';

interface AgentDef {
  id: string;
  label: string;
  shortLabel: string;
  icon: React.FC<any>;
  mission: string;
  logTemplate: (findings: any) => string[];
}

const AGENTS: AgentDef[] = [
  {
    id: 'intake',
    label: 'Evidence Intake Agent',
    shortLabel: 'EVIDENCE INTAKE',
    icon: Database,
    mission: 'Register and validate evidence. Generate SHA-256 custody chain.',
    logTemplate: (f) => [
      'Case registered with A.E.G.I.S. Orchestrator.',
      'SHA-256 cryptographic hash computed.',
      'Evidence metadata extracted.',
      'Custody chain established. ✓',
    ],
  },
  {
    id: 'privacy',
    label: 'Privacy Shield Agent',
    shortLabel: 'PRIVACY SHIELD',
    icon: Shield,
    mission: 'Protect investigators by detecting and redacting human subjects.',
    logTemplate: (f) => {
      const count = f?.count ?? 0;
      return count > 0
        ? [`${count} human subject${count > 1 ? 's' : ''} detected.`, 'Applying facial redaction masks.', 'Investigator-safe evidence output ready. ✓']
        : ['No human subjects detected in frame.', 'Evidence cleared for investigator review. ✓'];
    },
  },
  {
    id: 'enf',
    label: 'ENF Physics Agent',
    shortLabel: 'ENF PHYSICS',
    icon: Zap,
    mission: 'Verify physical authenticity using electrical network frequency analysis.',
    logTemplate: (f) => {
      const lines = ['Extracting luminance channel from evidence...', 'Applying Fast Fourier Transform (FFT)...', 'Computing Power Spectral Density (PSD)...'];
      if (f?.is_enf_available) {
        lines.push(`50Hz grid signature detected. Ratio: ${f.enf_ratio?.toFixed(2) ?? 'N/A'}`);
        lines.push(f.is_authentic ? 'Grid frequency AUTHENTIC. ✓' : 'Grid frequency ANOMALY detected. ⚠');
      } else {
        lines.push('ENF signal not available for this media type.');
        lines.push('Authenticity assessment deferred to other signals.');
      }
      return lines;
    },
  },
  {
    id: 'vision',
    label: 'Vision Intelligence Agent',
    shortLabel: 'VISION INTEL',
    icon: Eye,
    mission: 'Extract environmental intelligence from the scene using Gemini Vision.',
    logTemplate: (f) => {
      if (f?.status === 'offline') {
        return ['Gemini Vision: API key not configured on server.', 'Environmental extraction unavailable.', 'Knowledge Graph will operate without semantic entities.'];
      }
      const objs = f?.environmental_objects ?? [];
      const lines = ['Analyzing background environment...', `Scene type identified: ${f?.scene_type ?? 'Unknown'}`];
      if (objs.length > 0) {
        lines.push(`${objs.length} environmental entities extracted:`);
        objs.slice(0, 5).forEach((o: any) => lines.push(`  · ${o.entity ?? o}`));
        if (objs.length > 5) lines.push(`  · ...and ${objs.length - 5} more.`);
      }
      lines.push('Environmental intelligence extraction complete. ✓');
      return lines;
    },
  },
  {
    id: 'graph',
    label: 'Knowledge Graph Agent',
    shortLabel: 'KNOWLEDGE GRAPH',
    icon: GitBranch,
    mission: 'Correlate entities and map environmental relationships.',
    logTemplate: (f) => [
      'Initialising NetworkX investigation graph...',
      'Converting extracted entities to graph nodes...',
      'Establishing entity relationship edges...',
      'Investigation graph compiled. ✓',
    ],
  },
  {
    id: 'legal',
    label: 'Legal Report Agent',
    shortLabel: 'LEGAL REPORT',
    icon: FileText,
    mission: 'Generate a court-admissible BSA 2023 compliant forensic report.',
    logTemplate: (f) => [
      'Collecting forensic outputs from all agents...',
      'Computing final authenticity verdict...',
      'Attaching SHA-256 evidence hash...',
      'BSA 2023 statutory declaration generated. ✓',
    ],
  },
];

// Map API response fields to agent IDs
const AGENT_RESULT_MAP: Record<string, string> = {
  privacy: 'privacy',
  enf: 'enf',
  corneal: 'enf',       // corneal feeds enf agent display
  gemini: 'vision',
  knowledge_graph: 'graph',
  legal_report: 'legal',
};

const STATUS_CONFIG: Record<AgentStatus, { label: string; color: string; icon: React.FC<any> }> = {
  ready:     { label: 'READY',     color: 'text-textMuted border-border bg-surfaceHover',              icon: Circle },
  running:   { label: 'RUNNING',   color: 'text-primary border-primary/40 bg-primary/5',              icon: Loader2 },
  completed: { label: 'COMPLETED', color: 'text-success border-success/30 bg-success/5',              icon: CheckCircle2 },
  warning:   { label: 'WARNING',   color: 'text-accent border-accent/30 bg-accent/5',                 icon: AlertTriangle },
  failed:    { label: 'FAILED',    color: 'text-danger border-danger/30 bg-danger/5',                 icon: XCircle },
};

const Investigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as { mode: 'locker' | 'upload'; lockerFilename?: string; caseId?: string; evidenceName?: string } | null;

  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>(
    Object.fromEntries(AGENTS.map(a => [a.id, 'ready']))
  );
  const [orchestratorStatus, setOrchestratorStatus] = useState('Initialising investigation...');
  const [activityLog, setActivityLog] = useState<{ agent: string; lines: string[]; color: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [caseId, setCaseId] = useState<string>(state?.caseId ?? '');
  const hasStarted = useRef(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  const appendLog = (agentShort: string, lines: string[], color = 'text-primary') => {
    setActivityLog(prev => [...prev, { agent: agentShort, lines, color }]);
  };

  const setStatus = (id: string, status: AgentStatus) => {
    setAgentStatuses(prev => ({ ...prev, [id]: status }));
  };

  // Simulated streaming: reveal lines with typewriter cadence
  const streamLines = (agentShort: string, lines: string[], color: string, baseDelay = 400): Promise<void> => {
    return new Promise(resolve => {
      let i = 0;
      const tick = () => {
        if (i < lines.length) {
          setActivityLog(prev => {
            const last = prev[prev.length - 1];
            if (last?.agent === agentShort && last.color === color) {
              return [...prev.slice(0, -1), { agent: agentShort, lines: [...last.lines, lines[i]], color }];
            }
            return [...prev, { agent: agentShort, lines: [lines[i]], color }];
          });
          i++;
          setTimeout(tick, baseDelay + Math.random() * 200);
        } else {
          resolve();
        }
      };
      tick();
    });
  };

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    const run = async () => {
      // ── 1. Evidence Intake (immediate) ──────────────────────────
      setStatus('intake', 'running');
      setOrchestratorStatus('Dispatching Evidence Intake Agent...');
      await streamLines('EVIDENCE INTAKE', [
        'Case registered with A.E.G.I.S. Orchestrator.',
        'SHA-256 cryptographic hash computing...',
      ], 'text-primary');

      let result: any;
      try {
        if (state?.mode === 'locker') {
          result = await startInvestigation(state.lockerFilename!);
        } else {
          result = await analyzeEvidence(state?.caseId ?? '');
        }
      } catch (err: any) {
        const msg = err.response?.data?.detail || err.message || 'Unknown error';
        setError(msg);
        AGENTS.forEach(a => {
          if (agentStatuses[a.id] === 'running' || agentStatuses[a.id] === 'ready') {
            setStatus(a.id, 'failed');
          }
        });
        setOrchestratorStatus('Investigation halted — pipeline error.');
        return;
      }

      const resolvedCaseId = result.pipeline_status?.case_id ?? state?.caseId ?? '';
      setCaseId(resolvedCaseId);

      await streamLines('EVIDENCE INTAKE', [
        `Case ID assigned: ${resolvedCaseId}`,
        'Metadata extracted. Custody chain established. ✓',
      ], 'text-primary');
      setStatus('intake', 'completed');

      // ── 2. Privacy Shield ───────────────────────────────────────
      setStatus('privacy', 'running');
      setOrchestratorStatus('Dispatching Privacy Shield Agent...');
      const privacyFindings = result.privacy?.findings ?? {};
      const privacyLines = AGENTS[1].logTemplate(privacyFindings);
      await streamLines('PRIVACY SHIELD', privacyLines, 'text-cyan-400');
      setStatus('privacy', result.privacy?.status === 'failed' ? 'failed' : 'completed');

      // ── 3. ENF Physics ──────────────────────────────────────────
      setStatus('enf', 'running');
      setOrchestratorStatus('Dispatching ENF Physics Agent...');
      const enfFindings = result.enf?.findings ?? {};
      const enfLines = AGENTS[2].logTemplate(enfFindings);
      await streamLines('ENF PHYSICS', enfLines, 'text-yellow-400');
      const enfStatus = result.enf?.status === 'failed' ? 'failed'
        : result.enf?.status === 'warning' ? 'warning' : 'completed';
      setStatus('enf', enfStatus);

      // ── 4. Vision Intelligence ──────────────────────────────────
      setStatus('vision', 'running');
      setOrchestratorStatus('Dispatching Vision Intelligence Agent...');
      const visionFindings = result.gemini?.findings ?? {};
      const visionLines = AGENTS[3].logTemplate(visionFindings);
      await streamLines('VISION INTEL', visionLines, 'text-purple-400');
      const visionStatus = result.gemini?.status === 'failed' ? 'failed'
        : result.gemini?.status === 'warning' || visionFindings?.status === 'offline' ? 'warning' : 'completed';
      setStatus('vision', visionStatus);

      // ── 5. Knowledge Graph ──────────────────────────────────────
      setStatus('graph', 'running');
      setOrchestratorStatus('Dispatching Knowledge Graph Agent...');
      const graphLines = AGENTS[4].logTemplate(result.knowledge_graph?.findings ?? {});
      await streamLines('KNOWLEDGE GRAPH', graphLines, 'text-green-400');
      setStatus('graph', result.knowledge_graph?.status === 'failed' ? 'failed' : 'completed');

      // ── 6. Legal Report ─────────────────────────────────────────
      setStatus('legal', 'running');
      setOrchestratorStatus('Dispatching Legal Report Agent...');
      const legalLines = AGENTS[5].logTemplate(result.legal_report?.findings ?? {});
      await streamLines('LEGAL REPORT', legalLines, 'text-orange-400');
      setStatus('legal', 'completed');

      setOrchestratorStatus('Investigation complete. All agents have reported.');

      // Navigate to results after short pause
      setTimeout(() => {
        navigate(`/results/${resolvedCaseId}`, { state: { forensicData: result } });
      }, 2500);
    };

    run();
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activityLog]);

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Orchestrator Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="card mb-6 border-primary/20"
        style={{ background: 'linear-gradient(135deg, rgba(0,210,255,0.03) 0%, rgba(22,32,50,1) 100%)' }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Cpu className="w-10 h-10 text-primary" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full animate-ping" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-textMain tracking-wider">A.E.G.I.S. Orchestrator</h2>
              <p className="text-xs text-textMuted uppercase tracking-widest">Mission: Digital Evidence Investigation</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-textMuted uppercase tracking-wider mb-1">Status</p>
            <motion.p
              key={orchestratorStatus}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-sm font-medium text-primary font-mono"
            >
              {orchestratorStatus}
            </motion.p>
            {caseId && <p className="text-xs text-textMuted mt-1 font-mono">Case: <span className="text-primary">{caseId}</span></p>}
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-12 gap-6">
        {/* ── Agent Execution Timeline ── */}
        <div className="col-span-12 lg:col-span-5">
          <div className="card">
            <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-5">Mission Status · Agent Execution Timeline</p>
            <div className="space-y-1">
              {AGENTS.map((agent, idx) => {
                const status = agentStatuses[agent.id];
                const cfg = STATUS_CONFIG[status];
                const Icon = agent.icon;
                const StatusIcon = cfg.icon;
                const isLast = idx === AGENTS.length - 1;

                return (
                  <div key={agent.id}>
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className={`rounded-lg border p-4 transition-all duration-500 ${cfg.color}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${status === 'running' ? 'text-primary' : status === 'completed' ? 'text-success' : status === 'warning' ? 'text-accent' : status === 'failed' ? 'text-danger' : 'text-textMuted'}`} />
                          <div>
                            <p className="text-sm font-bold text-textMain">{agent.label}</p>
                            <p className="text-xs text-textMuted mt-0.5">{agent.mission}</p>
                          </div>
                        </div>
                        <div className={`flex items-center space-x-1.5 px-2 py-1 rounded text-xs font-bold border flex-shrink-0 ml-2 ${cfg.color}`}>
                          <StatusIcon className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`} />
                          <span>{cfg.label}</span>
                        </div>
                      </div>
                    </motion.div>
                    {!isLast && (
                      <div className="flex justify-center py-0.5">
                        <div className={`w-0.5 h-4 rounded transition-colors duration-500 ${
                          agentStatuses[AGENTS[idx + 1].id] !== 'ready' ? 'bg-primary/40' : 'bg-border'
                        }`} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── Live Activity Log ── */}
        <div className="col-span-12 lg:col-span-7">
          <div className="card h-full flex flex-col" style={{ minHeight: '560px' }}>
            <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-4">Live Agent Activity Log</p>
            <div className="flex-1 overflow-y-auto space-y-4 font-mono text-sm pr-1">
              <AnimatePresence>
                {activityLog.map((entry, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="border-l-2 border-border pl-3"
                  >
                    <p className={`text-xs font-bold uppercase tracking-widest mb-1 ${entry.color}`}>
                      [{entry.agent}]
                    </p>
                    {entry.lines.map((line, j) => (
                      <motion.p
                        key={j}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: j * 0.05 }}
                        className="text-secondary text-xs leading-relaxed"
                      >
                        {line}
                      </motion.p>
                    ))}
                  </motion.div>
                ))}
              </AnimatePresence>
              {activityLog.length === 0 && (
                <div className="flex items-center space-x-2 text-textMuted text-xs">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Awaiting agent dispatch...</span>
                </div>
              )}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 bg-danger/10 border border-danger/30 rounded-lg p-6 text-danger"
        >
          <div className="flex items-center space-x-3 mb-2">
            <XCircle className="w-6 h-6" />
            <h3 className="font-bold text-lg">Investigation Halted</h3>
          </div>
          <p className="font-mono text-sm opacity-90">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 bg-danger/20 hover:bg-danger/30 text-danger px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Return to Workspace
          </button>
        </motion.div>
      )}
    </div>
  );
};

export default Investigation;
