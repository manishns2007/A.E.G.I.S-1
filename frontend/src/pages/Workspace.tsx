import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, Zap, Eye, GitBranch, FileText, Database,
  Play, AlertCircle, CheckCircle, Clock, Film, ImageIcon,
  RefreshCw, Cpu, FolderArchive, Package,
  FileAudio, MessageSquare, HelpCircle, ChevronRight, FileText as FileDoc
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { registerCase, getLockerCases } from '../services/api';
import type { CaseLockerEntry, CaseRegistrationResponse } from '../services/api';


const AGENTS = [
  { id: 'intake',  label: 'Evidence Intake',     icon: Database,  mission: 'Register, hash, and inventory all case evidence.' },
  { id: 'privacy', label: 'Privacy Shield',      icon: Shield,    mission: 'Detect and redact human subjects.' },
  { id: 'enf',     label: 'ENF Physics',         icon: Zap,       mission: 'Verify authenticity via electrical network frequency.' },
  { id: 'vision',  label: 'Vision Intelligence', icon: Eye,       mission: 'Scene understanding via Gemini Vision AI.' },
  { id: 'graph',   label: 'Knowledge Graph',     icon: GitBranch, mission: 'Correlate entities into investigation graph.' },
  { id: 'legal',   label: 'Legal Report',        icon: FileText,  mission: 'Generate BSA 2023 court-admissible report.' },
];

type WorkspaceTab = 'locker' | 'register';

const InventoryBadge = ({ label, count, icon: Icon, color }: { label: string; count: number; icon: any; color: string }) => (
  <div className={`flex items-center justify-between p-3 rounded-lg border ${count > 0 ? 'border-border bg-surfaceHover' : 'border-border/40 bg-surface opacity-50'}`}>
    <div className="flex items-center space-x-2">
      <Icon className={`w-4 h-4 ${count > 0 ? color : 'text-textMuted'}`} />
      <span className="text-xs text-secondary">{label}</span>
    </div>
    <span className={`text-lg font-bold ${count > 0 ? 'text-textMain' : 'text-textMuted'}`}>{count}</span>
  </div>
);

const statusConfig: Record<string, { color: string; dot: string }> = {
  Ready:      { color: 'text-success', dot: 'bg-success' },
  Processing: { color: 'text-primary', dot: 'bg-primary animate-pulse' },
  Complete:   { color: 'text-accent', dot: 'bg-accent' },
  Error:      { color: 'text-danger', dot: 'bg-danger' },
};

const Workspace = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState<WorkspaceTab>('locker');
  const [cases, setCases] = useState<CaseLockerEntry[]>([]);
  const [lockerLoading, setLockerLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<CaseLockerEntry | null>(null);

  // Register tab state
  const [isDragging, setIsDragging] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registeredCase, setRegisteredCase] = useState<CaseRegistrationResponse | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);

  const fetchLocker = useCallback(async () => {
    setLockerLoading(true);
    try {
      const data = await getLockerCases();
      setCases(data);
    } catch {
      setCases([]);
    } finally {
      setLockerLoading(false);
    }
  }, []);

  useEffect(() => { fetchLocker(); }, [fetchLocker]);

  // ── Evidence Registration ────────────────────────────────────────────
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) await processRegistration(e.dataTransfer.files[0]);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) await processRegistration(e.target.files[0]);
    e.target.value = '';
  };

  const processRegistration = async (file: File) => {
    try {
      setRegisterError(null);
      setRegisteredCase(null);
      setIsRegistering(true);
      const result = await registerCase(file);
      setRegisteredCase(result);
      await fetchLocker();
    } catch (err: any) {
      setRegisterError(err.response?.data?.detail || err.message || 'Case registration failed');
    } finally {
      setIsRegistering(false);
    }
  };

  // ── Start Investigation ──────────────────────────────────────────────
  const handleStart = () => {
    const cid = registeredCase?.case_id || selectedCase?.case_id;
    const evidenceName = registeredCase?.name || selectedCase?.name;
    const inventory = registeredCase?.inventory || selectedCase?.inventory;
    if (!cid) return;
    navigate('/investigation', {
      state: { caseId: cid, evidenceName, inventory, totalFiles: registeredCase?.total_files || selectedCase?.total_files }
    });
  };

  const activeCase = registeredCase
    ? { case_id: registeredCase.case_id, name: registeredCase.name, inventory: registeredCase.inventory, total_files: registeredCase.total_files }
    : selectedCase
    ? { case_id: selectedCase.case_id, name: selectedCase.name, inventory: selectedCase.inventory, total_files: selectedCase.total_files }
    : null;

  const canStart = !!activeCase;

  return (
    <div className="min-h-screen bg-background p-6">

      {/* ── Header ── */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-textMain tracking-wider uppercase">Investigation Workspace</h2>
          <p className="text-secondary text-sm mt-0.5">Case-Based Multi-Agent Forensic Platform · Kerala Police Cyberdome</p>
        </div>
        <div className="flex items-center space-x-2 bg-surface border border-border rounded-lg px-4 py-2">
          <Cpu className="w-4 h-4 text-primary" />
          <span className="text-xs text-secondary uppercase tracking-wider">A.E.G.I.S. Orchestrator</span>
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-xs text-success font-semibold">Ready</span>
        </div>
      </motion.div>

      {/* ── Main Grid ── */}
      <div className="grid grid-cols-12 gap-6">

        {/* ═══ LEFT: Case Selection Panel ═══ */}
        <motion.div
          initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
          className="col-span-12 lg:col-span-7 card flex flex-col"
          style={{ minHeight: '500px' }}
        >
          {/* Tabs */}
          <div className="flex border-b border-border mb-5">
            <button
              onClick={() => setTab('locker')}
              className={`flex items-center space-x-2 px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
                tab === 'locker' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-secondary hover:text-textMain'
              }`}
            >
              <Database className="w-4 h-4" />
              <span>Evidence Locker</span>
              {cases.length > 0 && (
                <span className="bg-primary/20 text-primary text-xs font-bold px-1.5 py-0.5 rounded-full">{cases.length}</span>
              )}
            </button>
            <button
              onClick={() => { setTab('register'); setSelectedCase(null); }}
              className={`flex items-center space-x-2 px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
                tab === 'register' ? 'border-accent text-accent bg-accent/5' : 'border-transparent text-secondary hover:text-textMain'
              }`}
            >
              <FolderArchive className="w-4 h-4" />
              <span>Register Investigation</span>
            </button>
          </div>

          {/* ── Evidence Locker Tab ── */}
          <AnimatePresence mode="wait">
            {tab === 'locker' && (
              <motion.div key="locker" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-textMuted">Select an existing investigation to continue or dispatch agents</p>
                  <button onClick={fetchLocker} className="flex items-center space-x-1 text-xs text-textMuted hover:text-primary transition-colors">
                    <RefreshCw className="w-3 h-3" />
                    <span>Refresh</span>
                  </button>
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                  {lockerLoading ? (
                    <div className="flex justify-center items-center h-48">
                      <div className="w-8 h-8 border-2 border-border border-t-primary rounded-full animate-spin" />
                    </div>
                  ) : cases.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 text-textMuted">
                      <Database className="w-12 h-12 opacity-20 mb-3" />
                      <p className="font-medium">Evidence locker is empty</p>
                      <p className="text-sm mt-1">Register an investigation to get started</p>
                      <button onClick={() => setTab('register')} className="mt-4 btn-primary text-sm">
                        Register Investigation
                      </button>
                    </div>
                  ) : (
                    cases.map((c) => {
                      const sc = statusConfig[c.status] ?? statusConfig.Ready;
                      const isSelected = selectedCase?.case_id === c.case_id;
                      return (
                        <motion.div
                          key={c.case_id}
                          whileHover={{ scale: 1.005 }}
                          whileTap={{ scale: 0.995 }}
                          onClick={() => { setSelectedCase(c); setRegisteredCase(null); }}
                          className={`rounded-xl border p-4 cursor-pointer transition-all ${
                            isSelected
                              ? 'border-primary bg-primary/5 shadow-[0_0_15px_rgba(0,210,255,0.08)]'
                              : 'border-border hover:border-primary/40 bg-surfaceHover'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <Package className="w-5 h-5 text-accent flex-shrink-0" />
                              <div>
                                <p className="text-xs font-mono text-primary">{c.case_id}</p>
                                <p className="text-sm font-bold text-textMain truncate max-w-[260px]">{c.name}</p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-1.5 flex-shrink-0">
                              <span className={`w-2 h-2 rounded-full ${sc.dot}`} />
                              <span className={`text-xs font-bold ${sc.color}`}>{c.status}</span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4 text-xs text-textMuted">
                            <span className="flex items-center space-x-1">
                              <Clock className="w-3 h-3" />
                              <span>Registered {c.registered_at}</span>
                            </span>
                            <span className="flex items-center space-x-1 font-semibold text-secondary">
                              <FileDoc className="w-3 h-3" />
                              <span>{c.total_files} evidence file{c.total_files !== 1 ? 's' : ''}</span>
                            </span>
                            {c.inventory && (
                              <div className="flex items-center space-x-2">
                                {c.inventory.images > 0 && <span className="flex items-center space-x-0.5"><ImageIcon className="w-3 h-3 text-accent" /><span>{c.inventory.images}</span></span>}
                                {c.inventory.videos > 0 && <span className="flex items-center space-x-0.5"><Film className="w-3 h-3 text-primary" /><span>{c.inventory.videos}</span></span>}
                                {c.inventory.audio > 0  && <span className="flex items-center space-x-0.5"><FileAudio className="w-3 h-3 text-green-400" /><span>{c.inventory.audio}</span></span>}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      );
                    })
                  )}
                </div>
              </motion.div>
            )}

            {/* ── Register Investigation Tab ── */}
            {tab === 'register' && (
              <motion.div key="register" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col">
                <p className="text-xs text-textMuted mb-4">
                  Register a complete evidence package. Supports ZIP archives (automatically extracted) and individual media files.
                </p>

                {!registeredCase ? (
                  <div
                    onDragEnter={handleDrag} onDragLeave={handleDrag}
                    onDragOver={handleDrag} onDrop={handleDrop}
                    className={`relative flex-1 border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer group flex flex-col items-center justify-center ${
                      isDragging
                        ? 'border-accent bg-accent/5 shadow-[0_0_30px_rgba(255,183,3,0.1)]'
                        : 'border-border hover:border-primary/50 hover:bg-primary/3'
                    }`}
                  >
                    <input
                      type="file"
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                      accept=".zip,.mp4,.avi,.mov,.jpg,.jpeg,.png,.pdf,.txt,.json,.csv,.mp3,.wav,.aac"
                      onChange={handleFileSelect}
                      disabled={isRegistering}
                    />
                    {isRegistering ? (
                      <div className="flex flex-col items-center pointer-events-none">
                        <div className="w-14 h-14 border-4 border-border border-t-accent rounded-full animate-spin mb-5" />
                        <p className="text-lg font-bold text-textMain">Registering Case...</p>
                        <p className="text-secondary text-sm mt-1">Extracting archive · Inventorying evidence · Generating hash</p>
                      </div>
                    ) : (
                      <div className="pointer-events-none">
                        <FolderArchive className="w-16 h-16 text-textMuted group-hover:text-accent mx-auto mb-5 transition-colors" />
                        <p className="text-xl font-bold text-textMain mb-2">Register Evidence Package</p>
                        <p className="text-secondary mb-6">Drop a ZIP archive or single media file</p>
                        <div className="flex flex-wrap justify-center gap-2">
                          {['.zip (case package)', '.mp4 / .avi', '.jpg / .png', '.pdf / .txt', '.json / .csv'].map(fmt => (
                            <span key={fmt} className="bg-surfaceHover border border-border px-3 py-1 rounded text-xs text-secondary font-mono">{fmt}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  /* ── Case Registration Summary ── */
                  <motion.div
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex-1 flex flex-col"
                  >
                    <div className="bg-success/5 border border-success/30 rounded-xl p-5 mb-4">
                      <div className="flex items-center space-x-3 mb-3">
                        <CheckCircle className="w-7 h-7 text-success" />
                        <div>
                          <p className="text-success font-bold text-lg">Case Registered Successfully</p>
                          <p className="text-xs font-mono text-textMuted mt-0.5">{registeredCase.case_id}</p>
                        </div>
                      </div>
                      <p className="text-sm text-textMain font-medium mb-1">{registeredCase.name}</p>
                      <p className="text-xs text-textMuted">Primary evidence: <span className="font-mono text-primary">{registeredCase.primary_filename}</span></p>
                    </div>

                    <div className="mb-4">
                      <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-3">Evidence Inventory</p>
                      <div className="grid grid-cols-3 gap-2">
                        <InventoryBadge label="Images"    count={registeredCase.inventory.images}    icon={ImageIcon}    color="text-accent" />
                        <InventoryBadge label="Videos"    count={registeredCase.inventory.videos}    icon={Film}         color="text-primary" />
                        <InventoryBadge label="Audio"     count={registeredCase.inventory.audio}     icon={FileAudio}    color="text-green-400" />
                        <InventoryBadge label="Documents" count={registeredCase.inventory.documents} icon={FileDoc}      color="text-orange-400" />
                        <InventoryBadge label="Chats"     count={registeredCase.inventory.chats}     icon={MessageSquare} color="text-purple-400" />
                        <InventoryBadge label="Unknown"   count={registeredCase.inventory.unknown}   icon={HelpCircle}  color="text-textMuted" />
                      </div>
                      <div className="mt-3 bg-surfaceHover border border-border rounded-lg px-4 py-2 flex items-center justify-between">
                        <span className="text-sm text-secondary font-semibold">Total Evidence Files</span>
                        <span className="text-2xl font-bold text-textMain">{registeredCase.total_files}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => { setRegisteredCase(null); setRegisterError(null); }}
                      className="text-xs text-textMuted hover:text-primary transition-colors self-start"
                    >
                      ← Register a different package
                    </button>
                  </motion.div>
                )}

                {registerError && (
                  <div className="mt-3 flex items-center space-x-2 text-danger text-sm bg-danger/10 border border-danger/20 rounded-lg px-4 py-3">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <p>{registerError}</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* ═══ RIGHT: Queue + Agents ═══ */}
        <div className="col-span-12 lg:col-span-5 flex flex-col gap-5">

          {/* Investigation Queue */}
          <motion.div
            initial={{ opacity: 0, x: 15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
            className="card"
          >
            <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-4">Investigation Queue</p>

            {activeCase ? (
              <div className="mb-5">
                <div className="bg-surfaceHover border border-primary/20 rounded-xl p-4 mb-3">
                  <p className="text-xs text-primary font-bold uppercase tracking-wider mb-1">Active Case</p>
                  <p className="text-sm font-bold text-textMain truncate">{activeCase.name}</p>
                  <p className="text-xs font-mono text-textMuted mt-1">{activeCase.case_id}</p>

                  {/* Evidence summary */}
                  <div className="mt-3 pt-3 border-t border-border">
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-secondary">
                      {activeCase.inventory.images > 0    && <span className="flex items-center space-x-1"><ImageIcon className="w-3 h-3 text-accent"/><span>{activeCase.inventory.images} images</span></span>}
                      {activeCase.inventory.videos > 0    && <span className="flex items-center space-x-1"><Film className="w-3 h-3 text-primary"/><span>{activeCase.inventory.videos} videos</span></span>}
                      {activeCase.inventory.audio > 0     && <span className="flex items-center space-x-1"><FileAudio className="w-3 h-3 text-green-400"/><span>{activeCase.inventory.audio} audio</span></span>}
                      {activeCase.inventory.documents > 0 && <span className="flex items-center space-x-1"><FileDoc className="w-3 h-3 text-orange-400"/><span>{activeCase.inventory.documents} docs</span></span>}
                      {activeCase.inventory.chats > 0     && <span className="flex items-center space-x-1"><MessageSquare className="w-3 h-3 text-purple-400"/><span>{activeCase.inventory.chats} chats</span></span>}
                    </div>
                    <p className="text-xs font-bold text-textMain mt-2">{activeCase.total_files} total evidence file{activeCase.total_files !== 1 ? 's' : ''}</p>
                  </div>
                </div>

                <p className="text-xs text-textMuted text-center mb-1">
                  Dispatching 6 specialist agents · Analysis runs automatically
                </p>
              </div>
            ) : (
              <div className="mb-5 border border-dashed border-border rounded-xl p-6 text-center text-textMuted text-sm">
                <p>No investigation queued</p>
                <p className="text-xs mt-1">Select a case from the Evidence Locker or register a new package</p>
              </div>
            )}

            <motion.button
              whileHover={canStart ? { scale: 1.02, boxShadow: '0 0 25px rgba(0,210,255,0.25)' } : {}}
              whileTap={canStart ? { scale: 0.97 } : {}}
              onClick={handleStart}
              disabled={!canStart}
              className={`w-full flex items-center justify-center space-x-3 px-6 py-4 rounded-xl font-bold uppercase tracking-widest text-sm transition-all ${
                canStart ? 'bg-primary text-background cursor-pointer' : 'bg-surfaceHover text-textMuted cursor-not-allowed border border-border'
              }`}
            >
              <Play className="w-5 h-5" />
              <span>Start Investigation</span>
              {canStart && <ChevronRight className="w-4 h-4" />}
            </motion.button>
          </motion.div>

          {/* Assigned Agents */}
          <motion.div
            initial={{ opacity: 0, x: 15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
            className="card flex-1"
          >
            <p className="text-xs text-textMuted uppercase tracking-widest font-semibold mb-4">Assigned Specialist Agents</p>
            <div className="space-y-2">
              {AGENTS.map((agent, idx) => {
                const Icon = agent.icon;
                return (
                  <div key={agent.id} className="flex items-start space-x-3 p-2.5 rounded-lg bg-surfaceHover border border-border">
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <span className="text-xs text-textMuted font-mono w-4">{idx + 1}</span>
                      <Icon className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-textMain">{agent.label}</p>
                      <p className="text-xs text-textMuted">{agent.mission}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Workspace;
