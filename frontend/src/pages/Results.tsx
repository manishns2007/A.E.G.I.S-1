import { useState } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import {
  Shield, Zap, Eye, GitBranch, FileText,
  CheckCircle2, XCircle, AlertTriangle, Clock, Target,
  BarChart2
} from 'lucide-react';
import { motion } from 'framer-motion';
import Graph from '../components/Graph';

const AGENT_CARDS = [
  { key: 'privacy',       label: 'Privacy Shield',       icon: Shield,    color: 'text-cyan-400',   border: 'border-cyan-400/20',   bg: 'bg-cyan-400/5' },
  { key: 'enf',           label: 'ENF Physics',          icon: Zap,       color: 'text-yellow-400', border: 'border-yellow-400/20', bg: 'bg-yellow-400/5' },
  { key: 'corneal',       label: 'Corneal Topology',     icon: Eye,       color: 'text-blue-400', border: 'border-blue-400/20', bg: 'bg-blue-400/5' },
  { key: 'vision',        label: 'Vision Intelligence',  icon: Eye,       color: 'text-purple-400', border: 'border-purple-400/20', bg: 'bg-purple-400/5' },
  { key: 'risk',          label: 'Risk Assessment',      icon: AlertTriangle, color: 'text-red-400', border: 'border-red-400/20', bg: 'bg-red-400/5' },
  { key: 'fusion',        label: 'Intelligence Fusion',  icon: Target,    color: 'text-pink-400', border: 'border-pink-400/20', bg: 'bg-pink-400/5' },
  { key: 'graph',         label: 'Knowledge Graph',      icon: GitBranch, color: 'text-green-400',  border: 'border-green-400/20',  bg: 'bg-green-400/5' },
  { key: 'legal_report',  label: 'Legal Report',         icon: FileText,  color: 'text-orange-400', border: 'border-orange-400/20', bg: 'bg-orange-400/5' },
];

// Derive a human-readable key finding from agent outputs
const getKeyFinding = (key: string, agent: any): string => {
  const f = agent?.output ?? {};
  switch (key) {
    case 'privacy':
      return `${f.count ?? 0} subject${f.count !== 1 ? 's' : ''} redacted`;
    case 'enf':
      return f.is_enf_available
        ? (f.is_authentic ? `50Hz grid detected (${f.enf_ratio?.toFixed(2)})` : `Grid anomaly: ${f.enf_ratio?.toFixed(2)} ratio`)
        : 'ENF unavailable for this media';
    case 'corneal':
      return f.is_quality_sufficient
        ? `Symmetry: ${f.symmetry_score?.toFixed(1)}%`
        : (f.verdict_text ?? 'Quality insufficient');
    case 'vision':
      return f.status === 'offline'
        ? 'Vision Intel not configured'
        : `${f.environmental_objects?.length ?? 0} entities extracted`;
    case 'fusion':
      return f.verdict_badge ?? 'Synthesis complete';
    case 'graph':
      return f.historical_db_connected ? 'Graph with historical links' : 'Isolated case graph compiled';
    case 'risk':
      return `Risk Level: ${f.risk_level ?? 'UNKNOWN'}`;
    case 'legal_report':
      return f.verdict_badge ?? 'Report generated';
    default:
      return '—';
  }
};

const statusBadge = (status: string) => {
  const cfg: Record<string, string> = {
    success:  'bg-success/10 text-success border-success/20',
    warning:  'bg-accent/10 text-accent border-accent/20',
    failed:   'bg-danger/10 text-danger border-danger/20',
    unknown:  'bg-surfaceHover text-textMuted border-border',
  };
  return cfg[status] ?? cfg.unknown;
};

const Results = () => {
  const { caseId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const data = location.state?.forensicData;
  const [activeTab, setActiveTab] = useState('technical');

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <p className="text-secondary mb-4">No investigation data found.</p>
        <button onClick={() => navigate('/')} className="btn-primary">Return to Workspace</button>
      </div>
    );
  }

  const { privacy, enf, corneal, vision, graph, risk, fusion, legal_report } = data;
  const isAuthentic = legal_report?.output?.is_authentic;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      {/* ── Verdict Banner ── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`rounded-xl border-2 p-6 mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4 ${
          isAuthentic ? 'border-success bg-success/5' : 'border-danger bg-danger/5'
        }`}
      >
        <div className="flex items-center space-x-4">
          {isAuthentic
            ? <CheckCircle2 className="w-12 h-12 text-success flex-shrink-0" />
            : <XCircle className="w-12 h-12 text-danger flex-shrink-0" />
          }
          <div>
            <p className="text-xs text-textMuted uppercase tracking-widest mb-1">A.E.G.I.S. Forensic Verdict</p>
            <h2 className={`text-2xl font-bold ${isAuthentic ? 'text-success' : 'text-danger'}`}>
              {legal_report?.output?.verdict_badge ?? 'VERDICT UNAVAILABLE'}
            </h2>
            <p className="text-sm text-secondary mt-1">
              Determined by multi-agent forensic analysis · Case <span className="font-mono text-primary">{caseId}</span>
            </p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => navigate(`/report/${caseId}`)}
            className="flex items-center space-x-2 btn-primary"
          >
            <FileText className="w-4 h-4" />
            <span>View Legal Report</span>
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex items-center space-x-2 px-4 py-2 rounded border border-border text-secondary hover:text-textMain hover:border-primary/40 transition-colors text-sm font-medium"
          >
            <Target className="w-4 h-4" />
            <span>New Investigation</span>
          </button>
        </div>
      </motion.div>

      {/* ── Agent Summary Cards ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-4">Specialist Agent Results Summary</p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {AGENT_CARDS.map((agent) => {
            const agentData = data[agent.key];
            if (!agentData) return null;
            const Icon = agent.icon;
            const statusClass = statusBadge(agentData.status);
            return (
              <motion.div
                key={agent.key}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.15 }}
                className={`rounded-lg border p-3 ${agent.bg} ${agent.border}`}
              >
                <div className="flex items-center space-x-2 mb-3">
                  <Icon className={`w-4 h-4 ${agent.color}`} />
                  <span className={`text-xs font-bold ${agent.color}`}>{agent.label}</span>
                </div>
                <span className={`text-xs font-bold px-2 py-0.5 rounded border uppercase ${statusClass}`}>
                  {agentData.status}
                </span>
                <div className="mt-3 space-y-1">
                  <div className="flex items-center space-x-1 text-xs text-textMuted">
                    <Clock className="w-3 h-3" />
                    <span>{agentData.processing_time?.toFixed(2) ?? '—'}s</span>
                  </div>
                  {agentData.confidence != null && (
                    <div className="flex items-center space-x-1 text-xs text-textMuted">
                      <BarChart2 className="w-3 h-3" />
                      <span>{agentData.confidence?.toFixed(0)}%</span>
                    </div>
                  )}
                  <p className="text-xs text-textMain mt-2 leading-tight">
                    {getKeyFinding(agent.key, agentData)}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* ── Tabbed Detail View ── */}
      <div className="flex space-x-1 border-b border-border mb-6">
        {[
          { id: 'technical', label: 'Technical Forensics' },
          { id: 'intelligence', label: 'Environmental Intelligence' },
        ].map(tab => (
          <button
            key={tab.id}
            className={`px-6 py-3 font-medium transition-colors border-b-2 text-sm ${
              activeTab === tab.id
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-secondary hover:text-textMain'
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'technical' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Privacy */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <Shield className="w-5 h-5 text-cyan-400" />
              <h3 className="font-bold text-textMain">Privacy Shield Agent</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="metric-card">
                <div className="metric-label">Status</div>
                <div className="metric-value text-success">ACTIVE</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Subjects Redacted</div>
                <div className="metric-value">{privacy?.output?.count ?? 0}</div>
              </div>
            </div>
          </div>

          {/* ENF */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <Zap className="w-5 h-5 text-yellow-400" />
              <h3 className="font-bold text-textMain">ENF Physics Agent</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="metric-card">
                <div className="metric-label">Grid Verdict</div>
                <div className={`metric-value text-sm ${enf?.output?.is_authentic ? 'text-success' : 'text-danger'}`}>
                  {enf?.output?.verdict_text ?? 'N/A'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Peak/Noise Ratio</div>
                <div className="metric-value">{enf?.output?.enf_ratio?.toFixed(2) ?? '—'}</div>
              </div>
            </div>
          </div>

          {/* Corneal */}
          <div className="card md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <Eye className="w-5 h-5 text-purple-400" />
              <h3 className="font-bold text-textMain">Corneal Specular Topology Agent</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="metric-card">
                <div className="metric-label">Verdict</div>
                <div className={`metric-value text-sm ${corneal?.output?.is_authentic ? 'text-success' : 'text-danger'}`}>
                  {corneal?.output?.verdict_text ?? 'UNAVAILABLE'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Symmetry Score</div>
                <div className="metric-value">{corneal?.output?.symmetry_score?.toFixed(1) ?? '0.0'}%</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Quality Sufficient</div>
                <div className={`metric-value ${corneal?.output?.is_quality_sufficient ? 'text-success' : 'text-accent'}`}>
                  {corneal?.output?.is_quality_sufficient ? 'YES' : 'NO'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Anomaly Score</div>
                <div className="metric-value">{corneal?.output?.anomaly_score?.toFixed(1) ?? '—'}%</div>
              </div>
            </div>
            {corneal?.output?.explanation?.length > 0 && (
              <div className="mt-4 bg-surfaceHover border border-border rounded p-4">
                <p className="text-xs text-textMuted uppercase tracking-wider mb-2 font-semibold">Forensic Explanation</p>
                <ul className="space-y-1">
                  {corneal.output.explanation.slice(0, 5).map((exp: string, i: number) => (
                    <li key={i} className="text-xs text-secondary leading-relaxed">· {exp}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {/* Risk Assessment */}
          <div className="card md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h3 className="font-bold text-textMain">Risk Assessment Agent</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="metric-card">
                <div className="metric-label">Risk Level</div>
                <div className={`metric-value text-sm ${risk?.output?.risk_level === 'LOW' ? 'text-success' : risk?.output?.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-danger'}`}>
                  {risk?.output?.risk_level ?? 'UNAVAILABLE'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Confidence</div>
                <div className="metric-value">{risk?.confidence?.toFixed(1) ?? '0.0'}%</div>
              </div>
            </div>
            {risk?.output?.risk_factors?.length > 0 && (
              <div className="mt-4 bg-surfaceHover border border-border rounded p-4">
                <p className="text-xs text-textMuted uppercase tracking-wider mb-2 font-semibold">Risk Factors Identified</p>
                <ul className="space-y-1">
                  {risk.output.risk_factors.map((exp: string, i: number) => (
                    <li key={i} className="text-xs text-secondary leading-relaxed">· {exp}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {/* Fusion */}
          <div className="card md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <Target className="w-5 h-5 text-pink-400" />
              <h3 className="font-bold text-textMain">Intelligence Fusion Agent</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="metric-card">
                <div className="metric-label">Verdict</div>
                <div className={`metric-value text-sm ${fusion?.output?.is_authentic ? 'text-success' : 'text-danger'}`}>
                  {fusion?.output?.verdict_badge ?? 'UNAVAILABLE'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Confidence Score</div>
                <div className="metric-value">{fusion?.output?.overall_confidence?.toFixed(1) ?? '0.0'}%</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Active Vectors</div>
                <div className="metric-value">{fusion?.output?.active_vectors_count ?? 0}</div>
              </div>
            </div>
            {fusion?.output?.synthesized_reasoning?.length > 0 && (
              <div className="mt-4 bg-surfaceHover border border-border rounded p-4">
                <p className="text-xs text-textMuted uppercase tracking-wider mb-2 font-semibold">Synthesized Reasoning</p>
                <ul className="space-y-1">
                  {fusion.output.synthesized_reasoning.map((exp: string, i: number) => (
                    <li key={i} className="text-xs text-secondary leading-relaxed">· {exp}</li>
                  ))}
                </ul>
              </div>
            )}
            {fusion?.output?.investigative_leads?.length > 0 && (
              <div className="mt-4 bg-surfaceHover border border-border rounded p-4">
                <p className="text-xs text-textMuted uppercase tracking-wider mb-2 font-semibold">Investigative Leads</p>
                <ul className="space-y-1">
                  {fusion.output.investigative_leads.map((exp: string, i: number) => (
                    <li key={i} className="text-xs text-secondary leading-relaxed text-pink-400">· {exp}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'intelligence' && (
        <div className="space-y-6">
          {/* Knowledge Graph */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <GitBranch className="w-5 h-5 text-green-400" />
              <h3 className="font-bold text-textMain">Knowledge Graph Agent</h3>
            </div>
            <p className="text-sm text-secondary mb-4">Interactive mapping of extracted environmental entities.</p>
            <Graph caseId={caseId!} />
          </div>

          {/* Vision Intelligence */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <Eye className="w-5 h-5 text-purple-400" />
              <h3 className="font-bold text-textMain">Vision Intelligence Agent</h3>
            </div>
            {vision?.output?.status === 'offline' ? (
              <div className="flex items-center space-x-3 text-accent text-sm">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <p>{vision?.output?.error || 'Gemini Vision API not configured on server. Set the GEMINI_API_KEY environment variable to enable semantic extraction.'}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-textMuted uppercase mb-3">Extracted Entities</h4>
                  <div className="flex flex-wrap gap-2">
                    {vision?.output?.environmental_objects?.map((obj: any, idx: number) => (
                      <span key={idx} className="bg-surfaceHover border border-border px-3 py-1 rounded text-sm text-textMain">
                        {obj.entity ?? obj}
                      </span>
                    )) ?? <span className="text-secondary text-sm">No entities detected.</span>}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-textMuted uppercase mb-3">Scene Context</h4>
                  <div className="bg-surfaceHover border border-border rounded p-4 text-sm text-textMain space-y-2">
                    <p><span className="text-textMuted">Scene Type:</span> {vision?.output?.scene_type ?? 'Unknown'}</p>
                    <p><span className="text-textMuted">Spatial Layout:</span> {vision?.output?.spatial_layout ?? 'Unknown'}</p>
                    <p><span className="text-textMuted">Lighting:</span> {vision?.output?.lighting_type ?? 'Unknown'}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Results;
