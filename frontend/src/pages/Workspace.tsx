import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, Zap, Eye, GitBranch, FileText, Database,
  UploadCloud, Play, AlertCircle, CheckCircle, Clock,
  Film, ImageIcon, RefreshCw, Cpu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { uploadEvidence, getLockerItems, getSystemHealth, LockerItem, AgentHealth } from '../services/api';

const AGENTS = [
  { id: 'intake',   label: 'Evidence Intake Agent',      icon: Database,  mission: 'Register and validate evidence. Generate SHA-256 custody chain.' },
  { id: 'privacy',  label: 'Privacy Shield Agent',       icon: Shield,    mission: 'Protect investigators by detecting and redacting victims.' },
  { id: 'enf',      label: 'ENF Physics Agent',          icon: Zap,       mission: 'Verify physical authenticity using electrical network frequency analysis.' },
  { id: 'vision',   label: 'Vision Intelligence Agent',  icon: Eye,       mission: 'Extract environmental intelligence from the scene using Gemini Vision.' },
  { id: 'graph',    label: 'Knowledge Graph Agent',      icon: GitBranch, mission: 'Correlate entities and map environmental relationships.' },
  { id: 'legal',    label: 'Legal Report Agent',         icon: FileText,  mission: 'Generate a court-admissible BSA 2023 compliant forensic report.' },
];

const Workspace = () => {
  const navigate = useNavigate();
  const [lockerItems, setLockerItems] = useState<LockerItem[]>([]);
  const [health, setHealth] = useState<AgentHealth[]>([]);
  const [selectedLocker, setSelectedLocker] = useState<LockerItem | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [uploadedCase, setUploadedCase] = useState<{ case_id: string; filename: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lockerLoading, setLockerLoading] = useState(true);

  const fetchLocker = useCallback(async () => {
    try {
      setLockerLoading(true);
      const items = await getLockerItems();
      setLockerItems(items);
    } catch {
      setLockerItems([]);
    } finally {
      setLockerLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLocker();
    getSystemHealth().then(setHealth).catch(() => setHealth([]));
  }, [fetchLocker]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) await handleUpload(e.dataTransfer.files[0]);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) await handleUpload(e.target.files[0]);
  };

  const handleUpload = async (file: File) => {
    try {
      setError(null);
      setIsUploading(true);
      setSelectedLocker(null);
      const res = await uploadEvidence(file);
      setUploadedCase({ case_id: res.case_id, filename: file.name });
    } catch (err: any) {
      setError(err.message || 'Evidence registration failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartInvestigation = () => {
    if (selectedLocker) {
      setIsStarting(true);
      navigate('/investigation', { state: { mode: 'locker', lockerFilename: selectedLocker.filename, evidenceName: selectedLocker.filename } });
    } else if (uploadedCase) {
      setIsStarting(true);
      navigate(`/investigation`, { state: { mode: 'upload', caseId: uploadedCase.case_id, evidenceName: uploadedCase.filename } });
    }
  };

  const activeEvidence = selectedLocker?.filename || uploadedCase?.filename;
  const canStart = !!(selectedLocker || uploadedCase);

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-textMain tracking-wider uppercase">Investigation Workspace</h2>
            <p className="text-secondary text-sm mt-1">Multi-Agent Forensic Investigation Platform · Kerala Police Cyberdome</p>
          </div>
          <div className="flex items-center space-x-2 bg-surface border border-border rounded-lg px-4 py-2">
            <Cpu className="w-4 h-4 text-primary" />
            <span className="text-xs text-secondary uppercase tracking-wider">A.E.G.I.S. Orchestrator</span>
            <span className="w-2 h-2 rounded-full bg-success animate-pulse ml-1" />
            <span className="text-xs text-success font-semibold">Ready</span>
          </div>
        </div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">

        {/* ── EVIDENCE LOCKER ── */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="col-span-12 lg:col-span-5 card flex flex-col"
          style={{ minHeight: '420px' }}
        >
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center space-x-3">
              <Database className="w-5 h-5 text-accent" />
              <h3 className="font-bold text-textMain uppercase tracking-wider text-sm">Evidence Locker</h3>
            </div>
            <button onClick={fetchLocker} className="text-textMuted hover:text-primary transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto pr-1">
            {lockerLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-6 h-6 border-2 border-border border-t-primary rounded-full animate-spin" />
              </div>
            ) : lockerItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-textMuted text-sm">
                <Database className="w-8 h-8 mb-2 opacity-30" />
                <p>Evidence locker is empty</p>
              </div>
            ) : (
              lockerItems.map((item) => (
                <motion.div
                  key={item.filename}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => { setSelectedLocker(item); setUploadedCase(null); }}
                  className={`rounded-lg border p-3 cursor-pointer transition-all ${
                    selectedLocker?.filename === item.filename
                      ? 'border-primary bg-primary/5 shadow-[0_0_12px_rgba(0,210,255,0.1)]'
                      : 'border-border bg-surfaceHover hover:border-primary/40'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      {item.file_type === 'Video'
                        ? <Film className="w-5 h-5 text-primary flex-shrink-0" />
                        : <ImageIcon className="w-5 h-5 text-accent flex-shrink-0" />
                      }
                      <div>
                        <p className="text-xs font-mono text-primary mb-0.5">{item.case_ref}</p>
                        <p className="text-sm font-medium text-textMain truncate max-w-[200px]">{item.filename}</p>
                        <div className="flex items-center space-x-3 mt-1">
                          <span className="text-xs text-textMuted">{item.file_type}</span>
                          <span className="text-xs text-textMuted">{item.size_kb} KB</span>
                          <span className="flex items-center space-x-1 text-xs text-textMuted">
                            <Clock className="w-3 h-3" />
                            <span>{item.registered_at}</span>
                          </span>
                        </div>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-success bg-success/10 border border-success/20 px-2 py-0.5 rounded flex-shrink-0">
                      {item.status}
                    </span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>

        {/* ── RIGHT COLUMN ── */}
        <div className="col-span-12 lg:col-span-7 flex flex-col gap-6">

          {/* Assigned Agents */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
            className="card"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Cpu className="w-5 h-5 text-primary" />
              <h3 className="font-bold text-textMain uppercase tracking-wider text-sm">Assigned Specialist Agents</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {AGENTS.map((agent) => {
                const Icon = agent.icon;
                return (
                  <div key={agent.id} className="bg-surfaceHover border border-border rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-1.5">
                      <Icon className="w-4 h-4 text-primary flex-shrink-0" />
                      <span className="text-xs font-bold text-textMain leading-tight">{agent.label.replace(' Agent', '')}</span>
                    </div>
                    <p className="text-xs text-textMuted leading-relaxed">{agent.mission}</p>
                  </div>
                );
              })}
            </div>
          </motion.div>

          {/* Register Evidence + Queue */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <div className="flex items-center space-x-3 mb-4">
              <UploadCloud className="w-5 h-5 text-accent" />
              <h3 className="font-bold text-textMain uppercase tracking-wider text-sm">Register New Evidence</h3>
            </div>

            <div
              onDragEnter={handleDrag} onDragLeave={handleDrag}
              onDragOver={handleDrag} onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all ${
                isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'
              }`}
            >
              <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                accept=".mp4,.avi,.mov,.jpg,.jpeg,.png"
                onChange={handleFileSelect}
                disabled={isUploading}
              />
              {isUploading ? (
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 border-2 border-border border-t-primary rounded-full animate-spin mb-2" />
                  <p className="text-sm text-secondary">Establishing custody chain...</p>
                </div>
              ) : uploadedCase ? (
                <div className="flex flex-col items-center">
                  <CheckCircle className="w-8 h-8 text-success mb-2" />
                  <p className="text-sm font-medium text-success">Evidence Registered</p>
                  <p className="text-xs text-textMuted mt-1 font-mono">{uploadedCase.case_id} · {uploadedCase.filename}</p>
                </div>
              ) : (
                <>
                  <UploadCloud className="w-8 h-8 text-textMuted mx-auto mb-2" />
                  <p className="text-sm text-textMain">Drop evidence file here or click to browse</p>
                  <p className="text-xs text-textMuted mt-1">.mp4 · .avi · .jpg · .png</p>
                </>
              )}
            </div>

            {error && (
              <div className="mt-3 flex items-center space-x-2 text-danger text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}
          </motion.div>

          {/* Investigation Queue + Start */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="card border-border"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-1">Investigation Queue</p>
                {activeEvidence ? (
                  <p className="text-textMain font-medium">{activeEvidence}</p>
                ) : (
                  <p className="text-textMuted text-sm">No evidence selected — choose from locker or register new evidence</p>
                )}
              </div>
              <motion.button
                whileHover={canStart ? { scale: 1.03 } : {}}
                whileTap={canStart ? { scale: 0.97 } : {}}
                onClick={handleStartInvestigation}
                disabled={!canStart || isStarting}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-bold uppercase tracking-wider text-sm transition-all ${
                  canStart
                    ? 'bg-primary text-background hover:shadow-[0_0_20px_rgba(0,210,255,0.3)] cursor-pointer'
                    : 'bg-surfaceHover text-textMuted cursor-not-allowed border border-border'
                }`}
              >
                <Play className="w-4 h-4" />
                <span>{isStarting ? 'Dispatching...' : 'Start Investigation'}</span>
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* System Health */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="mt-6 card"
      >
        <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-4">System Health · Specialist Agent Subsystems</p>
        <div className="flex flex-wrap gap-4">
          {(health.length > 0 ? health : AGENTS.map(a => ({ name: a.label.replace(' Agent',''), status: 'online' as const }))).map((agent) => (
            <div key={agent.name} className="flex items-center space-x-2 bg-surfaceHover border border-border rounded-lg px-4 py-2">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${agent.status === 'online' ? 'bg-success animate-pulse' : 'bg-danger'}`} />
              <span className="text-xs text-secondary">{agent.name}</span>
              <span className={`text-xs font-bold ${agent.status === 'online' ? 'text-success' : 'text-danger'}`}>
                {agent.status.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Workspace;
