/**
 * A.E.G.I.S. Investigation Workspace — 3-Panel PoC Demo Interface
 *
 * LEFT   : Evidence Queue (upload, metadata, locker)
 * CENTER : Live Agent Activity (Planner card, agent terminal, growing graph, hypothesis timeline)
 * RIGHT  : Investigation Summary (6 goals, vectors, Evidence Gap Agent, Investigation Brief)
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Zap, Eye, GitBranch, FileText, Database, Cpu, AlertTriangle,
  CheckCircle2, Loader2, Circle, XCircle, Brain, Activity,
  TrendingUp, Search, Scale, BarChart3, ChevronRight, Clock,
  AlertCircle, ArrowRight, Layers, Target,
} from 'lucide-react';
import {
  streamInvestigation, startInvestigation,
  type MultiAgentInvestigationResponse,
  type PlannerStep,
  type ConfidencePoint,
  type KGGrowthStep,
  type InvestigationGoal,
  type SSEEvent,
} from '../services/api';

// ── Agent Definitions ─────────────────────────────────────────────────────────

const AGENT_DEF: Record<string, { label: string; shortLabel: string; icon: any; color: string }> = {
  EvidenceIntakeAgent:    { label: 'Evidence Intake Agent',    shortLabel: 'INTAKE',      icon: Database,      color: 'text-cyan-400'   },
  PrivacyShieldAgent:     { label: 'Privacy Shield Agent',     shortLabel: 'PRIVACY',     icon: Shield,        color: 'text-blue-400'   },
  ENFPhysicsAgent:        { label: 'ENF Physics Agent',        shortLabel: 'ENF',         icon: Zap,           color: 'text-yellow-400' },
  CornealTopologyAgent:   { label: 'Corneal Topology Agent',   shortLabel: 'CORNEAL',     icon: Eye,           color: 'text-purple-400' },
  VisionIntelligenceAgent: { label: 'Vision Intelligence Agent', shortLabel: 'VISION',   icon: Eye,           color: 'text-violet-400' },
  KnowledgeGraphAgent:    { label: 'Knowledge Graph Agent',    shortLabel: 'GRAPH',       icon: GitBranch,     color: 'text-green-400'  },
  RiskAssessmentAgent:    { label: 'Risk Assessment Agent',    shortLabel: 'RISK',        icon: AlertTriangle, color: 'text-red-400'    },
  IntelligenceFusionAgent: { label: 'Intelligence Fusion Agent', shortLabel: 'FUSION',  icon: Cpu,           color: 'text-pink-400'   },
  EvidenceGapAgent:       { label: 'Evidence Gap Agent',       shortLabel: 'GAP',         icon: Search,        color: 'text-orange-400' },
  LegalReasoningAgent:    { label: 'Legal Reasoning Agent',    shortLabel: 'LEGAL',       icon: Scale,         color: 'text-amber-400'  },
};

const AGENT_ORDER = [
  'EvidenceIntakeAgent', 'PrivacyShieldAgent', 'ENFPhysicsAgent', 'CornealTopologyAgent',
  'VisionIntelligenceAgent', 'KnowledgeGraphAgent', 'RiskAssessmentAgent',
  'IntelligenceFusionAgent', 'EvidenceGapAgent', 'LegalReasoningAgent',
];

type AgentStatus = 'pending' | 'running' | 'completed' | 'skipped' | 'failed' | 'warning';

// ── Log Entry ─────────────────────────────────────────────────────────────────

interface LogEntry {
  id: string;
  timestamp: string;
  agentKey: string;
  agentLabel: string;
  color: string;
  lines: string[];
  isPlanner?: boolean;
}

// ── Live Hypothesis Bar ───────────────────────────────────────────────────────

const HypothesisBar = ({ authentic, synthetic, label }: { authentic: number; synthetic: number; label?: string }) => {
  const authPct  = Math.round(authentic  * 100);
  const synthPct = Math.round(synthetic * 100);
  return (
    <div className="space-y-1.5">
      {label && <p className="text-xs text-textMuted uppercase tracking-widest">{label}</p>}
      <div className="flex items-center space-x-2">
        <span className="text-xs text-success w-16 font-mono">AUTH {authPct}%</span>
        <div className="flex-1 h-2 rounded-full bg-surfaceHover overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-success to-cyan-400 rounded-full"
            animate={{ width: `${authPct}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <span className="text-xs text-danger w-16 font-mono">SYNTH {synthPct}%</span>
        <div className="flex-1 h-2 rounded-full bg-surfaceHover overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-danger to-red-400 rounded-full"
            animate={{ width: `${synthPct}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
      </div>
    </div>
  );
};

// ── Planner Reasoning Card ────────────────────────────────────────────────────

const PlannerCard = ({ step }: { step: PlannerStep | null }) => {
  if (!step) return (
    <div className="rounded-lg border border-border bg-surface p-4 flex items-center space-x-3 text-textMuted">
      <Loader2 className="w-4 h-4 animate-spin" />
      <span className="text-sm">Awaiting planner initialisation…</span>
    </div>
  );

  const agentDef = AGENT_DEF[step.next_agent];
  const AgentIcon = agentDef?.icon ?? Brain;
  const agentColor = agentDef?.color ?? 'text-primary';

  return (
    <motion.div
      key={step.step}
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-primary/30 bg-gradient-to-br from-primary/5 to-surface p-4 space-y-3"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-primary" />
          <span className="text-xs font-bold text-primary uppercase tracking-widest">Planner · Step {step.step}</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          <span className="text-xs text-textMuted font-mono">{step.timestamp}</span>
        </div>
      </div>

      {/* Reasoning fields */}
      <div className="grid grid-cols-1 gap-2 text-xs">
        <div className="bg-surfaceHover rounded p-2.5 border border-border">
          <p className="text-textMuted uppercase tracking-wider mb-1 font-semibold text-[10px]">Current Goal</p>
          <p className="text-textMain leading-relaxed">{step.current_goal}</p>
        </div>
        <div className="bg-surfaceHover rounded p-2.5 border border-border">
          <p className="text-textMuted uppercase tracking-wider mb-1 font-semibold text-[10px]">Current Uncertainty</p>
          <p className="text-accent leading-relaxed">{step.current_uncertainty}</p>
        </div>
        <div className="bg-surfaceHover rounded p-2.5 border border-border">
          <p className="text-textMuted uppercase tracking-wider mb-1 font-semibold text-[10px]">Current Evidence</p>
          <p className="text-secondary leading-relaxed">{step.current_evidence}</p>
        </div>
      </div>

      {/* Decision */}
      <div className="border border-primary/20 rounded p-3 bg-primary/5">
        <div className="flex items-center space-x-2 mb-2">
          <ArrowRight className="w-3.5 h-3.5 text-primary" />
          <span className="text-[10px] uppercase tracking-widest text-textMuted font-semibold">Decision</span>
        </div>
        <div className="flex items-center space-x-2 mb-2">
          <AgentIcon className={`w-4 h-4 ${agentColor}`} />
          <span className={`text-sm font-bold ${agentColor}`}>
            Dispatch {step.next_agent === 'FINISH' ? 'FINISH' : step.next_agent === 'HUMAN_REVIEW' ? '⚠ HUMAN REVIEW' : (agentDef?.label ?? step.next_agent)}
          </span>
        </div>
        <p className="text-xs text-secondary leading-relaxed mb-1">
          <span className="text-textMuted font-semibold">Reason: </span>{step.reason}
        </p>
        <p className="text-xs text-secondary leading-relaxed">
          <span className="text-textMuted font-semibold">Expected: </span>{step.expected_benefit}
        </p>
      </div>

      {/* Hypothesis */}
      <div className="border border-border rounded p-2.5 bg-surfaceHover">
        <p className="text-[10px] uppercase tracking-widest text-textMuted mb-1.5 font-semibold">Updated Hypothesis</p>
        <p className="text-xs text-primary font-mono">{step.updated_hypothesis}</p>
      </div>
    </motion.div>
  );
};

// ── Main Component ────────────────────────────────────────────────────────────

interface WorkspaceState {
  caseId?: string;
  evidenceName?: string;
  inventory?: any;
  totalFiles?: number;
  isVideo?: boolean;
  sha256?: string;
  fileSize?: number;
  fps?: number;
  resolution?: string;
}

const InvestigationWorkspace = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as WorkspaceState | null;

  // ── Investigation state ─────────────────────────────────────────────────
  const [result, setResult] = useState<MultiAgentInvestigationResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Live planner ────────────────────────────────────────────────────────
  const [plannerSteps, setPlannerSteps] = useState<PlannerStep[]>([]);
  const [currentPlannerStep, setCurrentPlannerStep] = useState<PlannerStep | null>(null);

  // ── Agent statuses ──────────────────────────────────────────────────────
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>(
    Object.fromEntries(AGENT_ORDER.map(k => [k, 'pending']))
  );

  // ── Log stream ──────────────────────────────────────────────────────────
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);

  // ── Hypothesis evolution ────────────────────────────────────────────────
  const [confidenceHistory, setConfidenceHistory] = useState<ConfidencePoint[]>([]);
  const [currentHypo, setCurrentHypo] = useState({ authentic: 0.50, synthetic: 0.50 });

  // ── Knowledge graph ─────────────────────────────────────────────────────
  const [graphGrowth, setGraphGrowth] = useState<KGGrowthStep[]>([]);
  const [currentGraph, setCurrentGraph] = useState({ nodes: 0, edges: 0, entities: [] as string[] });

  // ── Goals ───────────────────────────────────────────────────────────────
  const [goals, setGoals] = useState<InvestigationGoal[]>([
    { goal: 'Authenticate Media',                 progress: 0,  status: 'IN_PROGRESS' },
    { goal: 'Protect Investigator',               progress: 0,  status: 'PENDING' },
    { goal: 'Extract Environmental Intelligence', progress: 0,  status: 'PENDING' },
    { goal: 'Correlate Evidence',                 progress: 0,  status: 'PENDING' },
    { goal: 'Assess Investigative Risk',          progress: 0,  status: 'PENDING' },
    { goal: 'Generate Legal Report',              progress: 0,  status: 'PENDING' },
  ]);

  // ── Evidence vectors ────────────────────────────────────────────────────
  const [activeVectors, setActiveVectors]   = useState<string[]>([]);
  const [missingVectors, setMissingVectors] = useState<string[]>([]);
  const [gapOutput, setGapOutput]           = useState<any>(null);
  const [brief, setBrief]                   = useState<any>(null);

  // ── Orchestrator status ─────────────────────────────────────────────────
  const [orchestratorStatus, setOrchestratorStatus] = useState('Initialising investigation workspace…');
  const [humanReviewRequired, setHumanReviewRequired] = useState(false);

  // ── Log append helper ───────────────────────────────────────────────────
  const addLog = useCallback((agentKey: string, lines: string[], isPlanner = false) => {
    const def = AGENT_DEF[agentKey];
    setLogEntries(prev => {
      const last = prev[prev.length - 1];
      if (last?.agentKey === agentKey) {
        return [...prev.slice(0, -1), { ...last, lines: [...last.lines, ...lines] }];
      }
      return [...prev, {
        id:         `${agentKey}-${Date.now()}`,
        timestamp:  new Date().toLocaleTimeString('en-US', { hour12: false }),
        agentKey,
        agentLabel: isPlanner ? 'PLANNER' : (def?.shortLabel ?? agentKey),
        color:      isPlanner ? 'text-primary' : (def?.color ?? 'text-textMain'),
        lines,
        isPlanner,
      }];
    });
  }, []);

  // ── Process SSE events ──────────────────────────────────────────────────
  const processEvent = useCallback((event: SSEEvent) => {
    switch (event.event) {
      case 'start':
        setOrchestratorStatus(`Investigation started — ${event.data.case_id}`);
        addLog('SYSTEM', ['Case registered. Dispatching LangGraph engine…'], false);
        break;

      case 'planner_step': {
        const step = event.data as PlannerStep;
        setPlannerSteps(prev => [...prev, step]);
        setCurrentPlannerStep(step);
        setOrchestratorStatus(`Planner Step ${step.step}: ${step.current_goal}`);
        addLog('PLANNER', [
          `[Step ${step.step}] ${step.current_goal}`,
          `Uncertainty: ${step.current_uncertainty}`,
          `→ Dispatching: ${step.next_agent}`,
          `Reason: ${step.reason}`,
        ], true);
        break;
      }

      case 'agent_start': {
        const { agent, timestamp } = event.data;
        const def = AGENT_DEF[agent];
        if (def) {
          setAgentStatuses(prev => ({ ...prev, [agent]: 'running' }));
          setOrchestratorStatus(`Dispatching ${def.label}…`);
          addLog(agent, [`▶ Agent dispatched at ${timestamp}`]);
        }
        break;
      }

      case 'log': {
        // Live reasoning lines from add_reasoning() calls inside agents
        const { agent, message } = event.data;
        const agentClass = Object.keys(AGENT_DEF).find(
          k => AGENT_DEF[k].label.toLowerCase().includes((agent ?? '').toLowerCase())
        ) ?? 'SYSTEM';
        if (message) addLog(agentClass, [message]);
        break;
      }

      case 'agent_done': {
        const { key, agent } = event.data;
        const agentName = agent?.agent ?? key;
        const agentClass = AGENT_ORDER.find(k => k.toLowerCase().includes(key?.replace('_', '').toLowerCase())) ?? key;

        const statusMap: Record<string, AgentStatus> = {
          completed: 'completed', skipped: 'skipped', failed: 'failed', warning: 'warning',
        };
        setAgentStatuses(prev => ({
          ...prev,
          [agentClass]: statusMap[agent?.status] ?? 'completed',
        }));

        // Emit agent reasoning to log
        const logKey = Object.keys(AGENT_DEF).find(k => AGENT_DEF[k].label === agentName) ?? agentClass;
        const lines = (agent?.reasoning ?? []).slice(0, 4);
        if (lines.length) addLog(logKey, lines);
        break;
      }

      case 'hypothesis': {
        const point = event.data as ConfidencePoint;
        setConfidenceHistory(prev => [...prev, point]);
        setCurrentHypo({ authentic: point.authentic_prob, synthetic: point.synthetic_prob });
        break;
      }

      case 'graph_update': {
        const growth = event.data as KGGrowthStep;
        setGraphGrowth(prev => [...prev, growth]);
        setCurrentGraph({ nodes: growth.nodes, edges: growth.edges, entities: growth.entities });
        addLog('KnowledgeGraphAgent', [
          `Graph updated: ${growth.nodes} nodes, ${growth.edges} edges`,
          growth.entities.length ? `Entities: ${growth.entities.slice(0, 4).join(', ')}` : 'No entities',
        ]);
        break;
      }

      case 'gap_analysis': {
        setGapOutput(event.data);
        break;
      }

      case 'complete': {
        const full = event.data as MultiAgentInvestigationResponse;
        setResult(full);
        setIsDone(true);
        setIsRunning(false);

        // Update all state from final payload
        if (full.goals)                 setGoals(full.goals as InvestigationGoal[]);
        if (full.active_vectors)        setActiveVectors(full.active_vectors);
        if (full.missing_vectors)       setMissingVectors(full.missing_vectors);
        if (full.confidence_evolution)  setConfidenceHistory(full.confidence_evolution);
        if (full.knowledge_graph_growth) setGraphGrowth(full.knowledge_graph_growth);
        if (full.planner_steps)         setPlannerSteps(full.planner_steps);
        if (full.investigation_brief)   setBrief(full.investigation_brief);
        if (full.evidence_gap?.output)  setGapOutput(full.evidence_gap.output);
        if (full.human_review_required) setHumanReviewRequired(true);

        if (full.hypotheses) {
          setCurrentHypo({
            authentic:  full.hypotheses['Authentic Media Record']   ?? 0.5,
            synthetic: full.hypotheses['Synthetic AI Fabrication']  ?? 0.5,
          });
        }

        // Mark all agent statuses
        const keyMap: Record<string, string> = {
          intake: 'EvidenceIntakeAgent', privacy: 'PrivacyShieldAgent',
          enf: 'ENFPhysicsAgent', corneal: 'CornealTopologyAgent',
          vision: 'VisionIntelligenceAgent', graph: 'KnowledgeGraphAgent',
          risk: 'RiskAssessmentAgent', fusion: 'IntelligenceFusionAgent',
          evidence_gap: 'EvidenceGapAgent', legal_report: 'LegalReasoningAgent',
        };
        Object.entries(keyMap).forEach(([key, cls]) => {
          const agentData = (full as any)[key];
          if (agentData) {
            const st = agentData.status ?? 'completed';
            setAgentStatuses(prev => ({ ...prev, [cls]: st as AgentStatus }));
          }
        });

        if (full.planner_steps?.length) {
          setCurrentPlannerStep(full.planner_steps[full.planner_steps.length - 1]);
        }

        setOrchestratorStatus('Investigation complete. All agents have reported.');
        addLog('SYSTEM', ['═══ INVESTIGATION COMPLETE ═══', `Court ready: ${full.court_ready}`, `Human review: ${full.human_review_required}`]);
        break;
      }

      case 'error': {
        setError(event.data?.message ?? 'Unknown error');
        setIsRunning(false);
        addLog('SYSTEM', [`ERROR: ${event.data?.message}`]);
        break;
      }
    }
  }, [addLog]);

  // ── Auto-start on mount ─────────────────────────────────────────────────
  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    const caseId = state?.caseId;
    if (!caseId) {
      setError('No case ID provided. Return to workspace and select a case.');
      return;
    }

    setIsRunning(true);
    setOrchestratorStatus('Connecting to A.E.G.I.S. pipeline…');

    const cleanup = streamInvestigation(
      caseId,
      processEvent,
      (err) => {
        console.error('SSE error', err);
        // Fallback to blocking call
        setOrchestratorStatus('Streaming unavailable — running blocking investigation…');
        startInvestigation(caseId).then(r => {
          processEvent({ event: 'complete', data: r });
        }).catch(e => {
          setError(String(e?.message ?? e));
          setIsRunning(false);
        });
      }
    );

    return cleanup;
  }, [state?.caseId, processEvent]);

  // ── Scroll log on new entries ───────────────────────────────────────────
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logEntries]);

  // ── Goal icon helper ────────────────────────────────────────────────────
  const GoalIcon = ({ status }: { status: string }) => {
    if (status === 'COMPLETED')   return <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />;
    if (status === 'IN_PROGRESS') return <Loader2 className="w-4 h-4 text-primary animate-spin flex-shrink-0" />;
    return <Circle className="w-4 h-4 text-textMuted flex-shrink-0" />;
  };

  const riskColors: Record<string, string> = {
    LOW: 'text-success', MEDIUM: 'text-accent', HIGH: 'text-orange-400',
    CRITICAL: 'text-danger', UNKNOWN: 'text-textMuted',
  };

  // ── LEFT PANEL: Evidence Queue ─────────────────────────────────────────
  const LeftPanel = () => (
    <div className="flex flex-col space-y-4">
      {/* Evidence card */}
      <div className="card">
        <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-3">Evidence Queue</p>
        <div className="space-y-2">
          <div className="flex items-center space-x-2 p-3 rounded-lg bg-surfaceHover border border-border">
            <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center flex-shrink-0">
              {state?.isVideo ? <Layers className="w-5 h-5 text-primary" /> : <Eye className="w-5 h-5 text-primary" />}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-textMain truncate">{state?.evidenceName ?? 'Evidence File'}</p>
              <p className="text-xs text-textMuted">{state?.isVideo ? 'Video' : 'Image'} · {state?.totalFiles ?? 1} file(s)</p>
            </div>
          </div>

          {/* Metadata rows */}
          {[
            { label: 'Case ID',   value: state?.caseId },
            { label: 'Media',     value: state?.isVideo ? 'VIDEO' : 'IMAGE' },
            { label: 'SHA-256',   value: result?.intake?.output?.sha256 ? `${result.intake.output.sha256.slice(0,12)}…` : 'Pending' },
            { label: 'Resolution', value: result?.intake?.output?.metadata?.resolution ?? 'Pending' },
            ...(state?.isVideo ? [{ label: 'FPS', value: result?.intake?.output?.metadata?.fps ? `${result.intake.output.metadata.fps} FPS` : 'Pending' }] : []),
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-1.5 border-b border-border/40 last:border-0">
              <span className="text-xs text-textMuted">{label}</span>
              <span className="text-xs text-textMain font-mono truncate max-w-[120px] text-right">{value ?? '—'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Agent pipeline status */}
      <div className="card">
        <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-3">Specialist Pipeline</p>
        <div className="space-y-1">
          {AGENT_ORDER.map((cls, i) => {
            const def    = AGENT_DEF[cls];
            const Icon   = def.icon;
            const status = agentStatuses[cls];
            const statusStyles: Record<AgentStatus, string> = {
              pending:   'text-textMuted border-border bg-surface',
              running:   'text-primary border-primary/40 bg-primary/5',
              completed: 'text-success border-success/30 bg-success/5',
              skipped:   'text-textMuted border-border/40 bg-surface opacity-50',
              failed:    'text-danger border-danger/30 bg-danger/5',
              warning:   'text-accent border-accent/30 bg-accent/5',
            };
            const StatusIcon = status === 'running' ? Loader2 : status === 'completed' ? CheckCircle2 : status === 'failed' ? XCircle : status === 'skipped' ? Circle : Circle;

            return (
              <motion.div
                key={cls}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`flex items-center justify-between px-3 py-2 rounded border text-xs transition-all duration-300 ${statusStyles[status]}`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className="w-3.5 h-3.5" />
                  <span className="font-medium">{def.shortLabel}</span>
                </div>
                <StatusIcon className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`} />
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Orchestrator status */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-2">
          <Cpu className="w-4 h-4 text-primary" />
          <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Orchestrator</p>
          {isRunning && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
          {isDone    && <CheckCircle2 className="w-3.5 h-3.5 text-success" />}
        </div>
        <motion.p key={orchestratorStatus} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs text-primary font-mono leading-relaxed">
          {orchestratorStatus}
        </motion.p>
        {humanReviewRequired && (
          <div className="mt-2 flex items-center space-x-2 p-2 rounded bg-accent/10 border border-accent/30">
            <AlertCircle className="w-3.5 h-3.5 text-accent flex-shrink-0" />
            <p className="text-xs text-accent">Human review required</p>
          </div>
        )}
      </div>
    </div>
  );

  // ── CENTER PANEL: Live Agent Activity ──────────────────────────────────
  const CenterPanel = () => (
    <div className="flex flex-col space-y-4 h-full">

      {/* Planner Reasoning Card */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-3">
          <Brain className="w-4 h-4 text-primary" />
          <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Live Planner Reasoning</p>
          {isRunning && plannerSteps.length > 0 && (
            <span className="ml-auto text-xs text-textMuted font-mono">{plannerSteps.length} steps</span>
          )}
        </div>
        <PlannerCard step={currentPlannerStep} />
      </div>

      {/* Live Agent Terminal */}
      <div className="card flex flex-col" style={{ minHeight: '280px' }}>
        <div className="flex items-center space-x-2 mb-3">
          <Activity className="w-4 h-4 text-primary" />
          <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Live Agent Terminal</p>
          {isRunning && <Loader2 className="w-3 h-3 text-primary animate-spin ml-auto" />}
        </div>
        <div className="flex-1 overflow-y-auto space-y-3 font-mono text-xs pr-1" style={{ maxHeight: '240px' }}>
          <AnimatePresence>
            {logEntries.map((entry) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="border-l-2 border-border pl-3"
              >
                <div className="flex items-center space-x-2 mb-0.5">
                  <span className={`font-bold uppercase text-[10px] tracking-widest ${entry.color}`}>
                    [{entry.agentLabel}]
                  </span>
                  <span className="text-textMuted text-[10px]">{entry.timestamp}</span>
                </div>
                {entry.lines.map((line, j) => (
                  <motion.p key={j} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: j * 0.05 }}
                    className="text-secondary leading-relaxed"
                  >
                    {line}
                  </motion.p>
                ))}
              </motion.div>
            ))}
          </AnimatePresence>
          {logEntries.length === 0 && (
            <div className="flex items-center space-x-2 text-textMuted">
              <Loader2 className="w-3 h-3 animate-spin" /><span>Awaiting agent dispatch…</span>
            </div>
          )}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* Hypothesis Evolution Timeline */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-3">
          <TrendingUp className="w-4 h-4 text-primary" />
          <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Hypothesis Evolution</p>
        </div>
        <HypothesisBar authentic={currentHypo.authentic} synthetic={currentHypo.synthetic} label="Current" />
        {confidenceHistory.length > 1 && (
          <div className="mt-3 space-y-1 max-h-32 overflow-y-auto">
            {confidenceHistory.map((pt, i) => {
              const def = AGENT_DEF[pt.agent];
              return (
                <div key={i} className="flex items-center space-x-2 text-[10px] font-mono text-textMuted">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${Math.round(pt.authentic_prob * 100) > 60 ? 'bg-success' : 'bg-danger'}`} />
                  <span className={def?.color ?? 'text-textMuted'}>{def?.shortLabel ?? pt.agent}</span>
                  <span className="flex-1 border-b border-border/30" />
                  <span className="text-success">AUTH {Math.round(pt.authentic_prob * 100)}%</span>
                  <span className="text-danger">SYN {Math.round(pt.synthetic_prob * 100)}%</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Knowledge Graph Growth */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-3">
          <GitBranch className="w-4 h-4 text-primary" />
          <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Knowledge Graph Growth</p>
          <span className="ml-auto text-xs font-mono text-success">{currentGraph.nodes} nodes · {currentGraph.edges} edges</span>
        </div>
        {currentGraph.entities.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            <AnimatePresence>
              {currentGraph.entities.map((ent, i) => (
                <motion.span
                  key={ent}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.08 }}
                  className="px-2 py-0.5 rounded-full border border-green-400/30 bg-green-400/5 text-green-400 text-[10px] font-mono"
                >
                  {ent}
                </motion.span>
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <p className="text-xs text-textMuted italic">Awaiting Vision Intelligence entity extraction…</p>
        )}
        {graphGrowth.length > 1 && (
          <div className="mt-3 flex items-end space-x-1 h-10">
            {graphGrowth.map((g, i) => (
              <motion.div
                key={i}
                className="flex-1 bg-green-400/30 rounded-sm"
                style={{
                  height: `${Math.min(100, (g.nodes / Math.max(1, graphGrowth[graphGrowth.length - 1].nodes)) * 100)}%`,
                  transformOrigin: 'bottom'
                }}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                title={`Step ${g.step}: ${g.nodes} nodes`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );

  // ── RIGHT PANEL: Investigation Summary ─────────────────────────────────
  const RightPanel = () => {
    const gapData = gapOutput ?? result?.evidence_gap?.output;
    const briefData = brief ?? result?.investigation_brief;
    const riskLevel = briefData?.risk_level ?? result?.risk?.output?.risk_level ?? 'UNKNOWN';
    const fusion = result?.fusion?.output;
    const verdictBadge = fusion?.verdict_badge ?? briefData?.verdict ?? '';

    return (
      <div className="flex flex-col space-y-4">

        {/* 6 Investigation Goals */}
        <div className="card">
          <div className="flex items-center space-x-2 mb-3">
            <Target className="w-4 h-4 text-primary" />
            <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Investigation Goals</p>
          </div>
          <div className="space-y-2">
            {goals.map((g, i) => (
              <div key={i} className="flex items-center space-x-2">
                <GoalIcon status={g.status} />
                <div className="flex-1">
                  <p className={`text-xs ${g.status === 'COMPLETED' ? 'text-textMain' : g.status === 'IN_PROGRESS' ? 'text-primary' : 'text-textMuted'}`}>
                    {g.goal}
                  </p>
                  {g.status === 'IN_PROGRESS' && (
                    <div className="mt-0.5 h-1 rounded-full bg-surfaceHover overflow-hidden">
                      <motion.div
                        className="h-full bg-primary rounded-full"
                        animate={{ width: `${g.progress}%` }}
                        transition={{ duration: 0.4 }}
                      />
                    </div>
                  )}
                </div>
                <span className={`text-[10px] font-mono ${g.status === 'COMPLETED' ? 'text-success' : g.status === 'IN_PROGRESS' ? 'text-primary' : 'text-textMuted'}`}>
                  {g.status === 'COMPLETED' ? '✔' : g.status === 'IN_PROGRESS' ? '…' : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence Vectors */}
        <div className="card">
          <div className="flex items-center space-x-2 mb-3">
            <BarChart3 className="w-4 h-4 text-primary" />
            <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Evidence Vectors</p>
          </div>
          {gapData ? (
            <div className="space-y-1.5">
              {gapData.available_vectors?.map((v: any, i: number) => (
                <div key={i} className="flex items-start space-x-2 p-2 rounded bg-success/5 border border-success/20">
                  <CheckCircle2 className="w-3.5 h-3.5 text-success flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-textMain font-semibold">{v.vector}</p>
                    <p className="text-[10px] text-textMuted">{v.finding}</p>
                  </div>
                </div>
              ))}
              {gapData.missing_vectors?.map((v: any, i: number) => (
                <div key={i} className="flex items-start space-x-2 p-2 rounded bg-danger/5 border border-danger/20">
                  <XCircle className="w-3.5 h-3.5 text-danger flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-textMain font-semibold">{v.vector}</p>
                    <p className="text-[10px] text-textMuted">{v.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-1.5">
              {activeVectors.map((v, i) => (
                <div key={i} className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3 h-3 text-success flex-shrink-0" />
                  <span className="text-xs text-secondary">{v}</span>
                </div>
              ))}
              {missingVectors.map((v, i) => (
                <div key={i} className="flex items-center space-x-2">
                  <XCircle className="w-3 h-3 text-danger flex-shrink-0" />
                  <span className="text-xs text-textMuted">{v}</span>
                </div>
              ))}
              {!activeVectors.length && !missingVectors.length && (
                <p className="text-xs text-textMuted italic">Evidence vectors loading…</p>
              )}
            </div>
          )}
        </div>

        {/* Evidence Gap Agent */}
        {gapData && (
          <div className="card border border-orange-400/20">
            <div className="flex items-center space-x-2 mb-3">
              <Search className="w-4 h-4 text-orange-400" />
              <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Evidence Gap Agent</p>
            </div>
            <div className="flex items-center justify-between mb-3">
              <div className="text-center">
                <p className="text-lg font-bold text-textMain">{gapData.current_confidence?.toFixed(1)}%</p>
                <p className="text-[10px] text-textMuted">Current</p>
              </div>
              <ArrowRight className="w-4 h-4 text-textMuted" />
              <div className="text-center">
                <p className="text-lg font-bold text-success">{gapData.estimated_confidence_after?.toFixed(1)}%</p>
                <p className="text-[10px] text-textMuted">Achievable</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-bold text-textMain">{gapData.investigation_completeness?.toFixed(0)}%</p>
                <p className="text-[10px] text-textMuted">Complete</p>
              </div>
            </div>
            {gapData.human_review_required && (
              <div className="mb-3 flex items-center space-x-2 p-2 rounded bg-accent/10 border border-accent/30">
                <AlertCircle className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                <p className="text-xs text-accent font-semibold">Human investigator review required</p>
              </div>
            )}
            {gapData.recommendations?.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-[10px] uppercase tracking-widest text-textMuted font-semibold">Recommendations</p>
                {gapData.recommendations.slice(0, 3).map((r: string, i: number) => (
                  <div key={i} className="flex items-start space-x-1.5">
                    <ChevronRight className="w-3 h-3 text-orange-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-secondary leading-relaxed">{r}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Investigation Brief */}
        {briefData && (
          <div className="card border border-primary/20">
            <div className="flex items-center space-x-2 mb-3">
              <FileText className="w-4 h-4 text-primary" />
              <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">Investigation Brief</p>
            </div>

            {/* Verdict badge */}
            {verdictBadge && (
              <div className={`mb-3 p-2.5 rounded border ${verdictBadge.includes('AUTHENTIC') ? 'border-success/30 bg-success/5' : verdictBadge.includes('SYNTHETIC') ? 'border-danger/30 bg-danger/5' : 'border-border bg-surfaceHover'}`}>
                <p className={`text-xs font-bold ${verdictBadge.includes('AUTHENTIC') ? 'text-success' : verdictBadge.includes('SYNTHETIC') ? 'text-danger' : 'text-textMain'}`}>
                  {verdictBadge}
                </p>
              </div>
            )}

            {/* Risk level */}
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-textMuted">Risk Level</span>
              <span className={`text-xs font-bold ${riskColors[riskLevel] ?? 'text-textMuted'}`}>{riskLevel}</span>
            </div>

            {/* Summary paragraphs */}
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {briefData.summary_paragraphs?.map((p: string, i: number) => (
                <p key={i} className="text-xs text-secondary leading-relaxed border-l-2 border-border pl-2">{p}</p>
              ))}
            </div>

            {/* Recommended next action */}
            {briefData.recommended_next_action && (
              <div className="mt-3 p-2.5 rounded bg-surfaceHover border border-border">
                <p className="text-[10px] uppercase tracking-widest text-textMuted mb-1 font-semibold">Recommended Next Action</p>
                <p className="text-xs text-textMain">{briefData.recommended_next_action}</p>
              </div>
            )}

            {/* Legal admissibility */}
            <div className="mt-2 p-2.5 rounded bg-surfaceHover border border-border">
              <p className="text-[10px] uppercase tracking-widest text-textMuted mb-1 font-semibold">Legal Admissibility</p>
              <p className="text-xs text-primary">{briefData.legal_admissibility}</p>
            </div>

            {isDone && result?.legal_report?.output?.html_content && (
              <button
                onClick={() => navigate(`/report/${state?.caseId}`, { state: { forensicData: result } })}
                className="mt-3 w-full btn-primary text-xs py-2"
              >
                View Full BSA 2023 Certificate
              </button>
            )}
          </div>
        )}

        {/* Loading skeleton for brief */}
        {!briefData && isRunning && (
          <div className="card border border-border animate-pulse">
            <div className="h-3 bg-surfaceHover rounded w-3/4 mb-3" />
            <div className="h-2 bg-surfaceHover rounded w-full mb-2" />
            <div className="h-2 bg-surfaceHover rounded w-5/6 mb-2" />
            <div className="h-2 bg-surfaceHover rounded w-4/6" />
          </div>
        )}
      </div>
    );
  };

  // ── Error State ────────────────────────────────────────────────────────
  if (error) return (
    <div className="min-h-screen bg-background p-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl mx-auto mt-20 bg-danger/10 border border-danger/30 rounded-xl p-8"
      >
        <div className="flex items-center space-x-3 mb-3">
          <XCircle className="w-7 h-7 text-danger" />
          <h2 className="text-lg font-bold text-danger">Investigation Error</h2>
        </div>
        <p className="font-mono text-sm text-danger/90 mb-5">{error}</p>
        <button onClick={() => navigate('/')} className="btn-primary">Return to Workspace</button>
      </motion.div>
    </div>
  );

  // ── Main Layout ────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background">
      {/* Investigation header bar */}
      <div className="border-b border-border bg-surface px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Brain className="w-6 h-6 text-primary" />
            {isRunning && <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-primary rounded-full animate-ping" />}
          </div>
          <div>
            <h2 className="text-sm font-bold text-textMain tracking-wider uppercase">Investigation Workspace</h2>
            <p className="text-xs text-textMuted font-mono">{state?.caseId ?? 'No case loaded'}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="text-textMuted">Planner Steps:</span>
            <span className="font-mono text-primary">{plannerSteps.length}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="text-textMuted">Agents:</span>
            <span className="font-mono text-success">{Object.values(agentStatuses).filter(s => s === 'completed').length}</span>
            <span className="text-textMuted">/</span>
            <span className="font-mono text-textMain">{AGENT_ORDER.length}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5 text-textMuted" />
            <span className="text-textMuted">{new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
          </div>
          {isDone && (
            <div className="flex items-center space-x-1.5 text-success">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Complete</span>
            </div>
          )}
          {isRunning && (
            <div className="flex items-center space-x-1.5 text-primary">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Investigating…</span>
            </div>
          )}
        </div>
      </div>

      {/* 3-Panel Layout */}
      <div className="grid grid-cols-12 gap-4 p-4" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {/* LEFT: Evidence Queue */}
        <div className="col-span-12 lg:col-span-3 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 140px)' }}>
          <LeftPanel />
        </div>

        {/* CENTER: Live Agent Activity */}
        <div className="col-span-12 lg:col-span-5 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 140px)' }}>
          <CenterPanel />
        </div>

        {/* RIGHT: Investigation Summary */}
        <div className="col-span-12 lg:col-span-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 140px)' }}>
          <RightPanel />
        </div>
      </div>
    </div>
  );
};

export default InvestigationWorkspace;
