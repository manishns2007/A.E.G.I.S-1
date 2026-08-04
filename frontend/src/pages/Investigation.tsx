import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Shield, Zap, Eye, GitBranch, FileText, Cpu,
  CheckCircle2, Loader2, Circle, AlertTriangle, XCircle
} from 'lucide-react';
import { startInvestigation } from '../services/api';
import type { EvidenceInventory } from '../services/api';

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
    logTemplate: (_f: any) => [],
  },
  {
    id: 'privacy',
    label: 'Privacy Shield Agent',
    shortLabel: 'PRIVACY SHIELD',
    icon: Shield,
    mission: 'Protect investigators by detecting and redacting human subjects.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'enf',
    label: 'ENF Physics Agent',
    shortLabel: 'ENF PHYSICS',
    icon: Zap,
    mission: 'Verify physical authenticity using electrical network frequency analysis.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'corneal',
    label: 'Corneal Topology Agent',
    shortLabel: 'CORNEAL TOPOLOGY',
    icon: Eye,
    mission: 'Analyze corneal specular highlights for environmental lighting consistency.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'vision',
    label: 'Vision Intelligence Agent',
    shortLabel: 'VISION INTEL',
    icon: Eye,
    mission: 'Extract environmental intelligence from the scene using Gemini Vision.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'graph',
    label: 'Knowledge Graph Agent',
    shortLabel: 'KNOWLEDGE GRAPH',
    icon: GitBranch,
    mission: 'Correlate entities and map environmental relationships.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'risk',
    label: 'Risk Assessment Agent',
    shortLabel: 'RISK ASSESSMENT',
    icon: AlertTriangle,
    mission: 'Evaluate forensic findings to assign a comprehensive case risk level.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'fusion',
    label: 'Intelligence Fusion Agent',
    shortLabel: 'INTEL FUSION',
    icon: Cpu,
    mission: 'Synthesize multi-vector outputs into a unified authenticity verdict.',
    logTemplate: (_f: any) => [],
  },
  {
    id: 'legal',
    label: 'Legal Report Agent',
    shortLabel: 'LEGAL REPORT',
    icon: FileText,
    mission: 'Generate a court-admissible BSA 2023 compliant forensic report.',
    logTemplate: (_f: any) => [],
  },
];

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
  const state = location.state as {
    caseId?: string;
    evidenceName?: string;
    inventory?: EvidenceInventory;
    totalFiles?: number;
    // legacy
    mode?: string;
    lockerFilename?: string;
  } | null;

  const inventory = state?.inventory;

  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>(
    Object.fromEntries(AGENTS.map(a => [a.id, 'ready']))
  );
  const [orchestratorStatus, setOrchestratorStatus] = useState('Initialising investigation...');
  const [activityLog, setActivityLog] = useState<{ agent: string; lines: string[]; color: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [caseId, setCaseId] = useState<string>(state?.caseId ?? '');
  const hasStarted = useRef(false);
  const logEndRef = useRef<HTMLDivElement>(null);


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
      let result: any;
      try {
        const activeCaseId = state?.caseId ?? '';
        if (activeCaseId) {
          result = await startInvestigation(activeCaseId);
        } else {
          throw new Error('No case ID provided to Investigation page.');
        }
      } catch (err: any) {
        const msg = err.response?.data?.detail || err.message || 'Unknown error';
        setError(msg);
        AGENTS.forEach(_a => setStatus(_a.id, 'failed'));
        setOrchestratorStatus('Investigation halted — pipeline error.');
        return;
      }

      const resolvedCaseId = result.case_id ?? state?.caseId ?? '';
      setCaseId(resolvedCaseId);

      // Parse and stream the reasoning chain from the backend
      const chain: string[] = result.reasoning_chain ?? [];
      
      // We will parse the agent names to match UI states
      const mapAgentNameToId: Record<string, string> = {
        'EVIDENCE INTAKE AGENT': 'intake',
        'PRIVACY SHIELD AGENT': 'privacy',
        'ENF PHYSICS AGENT': 'enf',
        'CORNEAL TOPOLOGY AGENT': 'corneal',
        'VISION INTELLIGENCE AGENT': 'vision',
        'KNOWLEDGE GRAPH AGENT': 'graph',
        'RISK ASSESSMENT AGENT': 'risk',
        'INTELLIGENCE FUSION AGENT': 'fusion',
        'LEGAL REASONING AGENT': 'legal',
      };

      for (const line of chain) {
        // Line format: "[Planner] Message" or "[Privacy Shield Agent] Message"
        const match = line.match(/^\[(.*?)\] (.*)$/);
        if (match) {
          const rawAgent = match[1];
          const msg = match[2];
          
          let displayAgent = rawAgent.toUpperCase();
          let color = 'text-primary';
          
          if (rawAgent === 'Planner') {
             displayAgent = 'PLANNER';
             color = 'text-white';
             setOrchestratorStatus(msg);
          } else {
             const id = mapAgentNameToId[rawAgent];
             if (id) {
                // Set the current running agent
                setStatus(id, 'running');
                displayAgent = AGENTS.find(a => a.id === id)?.shortLabel || rawAgent.toUpperCase();
                
                if (id === 'privacy') color = 'text-cyan-400';
                else if (id === 'enf') color = 'text-yellow-400';
                else if (id === 'corneal') color = 'text-blue-400';
                else if (id === 'vision') color = 'text-purple-400';
                else if (id === 'graph') color = 'text-green-400';
                else if (id === 'risk') color = 'text-red-400';
                else if (id === 'fusion') color = 'text-pink-400';
                else if (id === 'legal') color = 'text-orange-400';
             }
          }
          
          await streamLines(displayAgent, [msg], color, 100);
        } else {
          // Unformatted line
          await streamLines('SYSTEM', [line], 'text-textMuted', 100);
        }
      }

      // After streaming, update all final statuses based on the result payload
      AGENTS.forEach(a => {
         const backendId = a.id === 'legal' ? 'legal_report' : a.id;
         const agentData = result[backendId];
         if (agentData) {
            const status = agentData.status; // 'completed', 'skipped', 'failed', 'warning'
            setStatus(a.id, status === 'failed' ? 'failed' : status === 'skipped' ? 'skipped' : status === 'warning' ? 'warning' : 'completed');
            
            // Render skip reason if applicable
            if (status === 'skipped' && agentData.output?.verdict_text) {
                streamLines(a.shortLabel, [`Skipped: ${agentData.output.verdict_text}`], 'text-textMuted', 0);
            }
         }
      });

      setOrchestratorStatus('Investigation complete. All agents have reported.');

      // Navigate to results after short pause
      setTimeout(() => {
        navigate(`/results/${resolvedCaseId}`, { state: { forensicData: result } });
      }, 3000);
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
