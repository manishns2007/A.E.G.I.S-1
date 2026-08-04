import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, CircleDashed, Loader2, AlertCircle } from 'lucide-react';
import { analyzeEvidence } from '../services/api';

const STAGES = [
  { id: 'privacy', label: 'Agentic Privacy Shield' },
  { id: 'enf', label: 'ENF Physics Engine' },
  { id: 'corneal', label: 'Corneal Specular Topology' },
  { id: 'gemini', label: 'Semantic Scene Interpretation' },
  { id: 'knowledge_graph', label: 'Visuo-Acoustic Knowledge Graphing' },
  { id: 'legal_report', label: 'Dynamic Legal Docket Generation' }
];

const Processing = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [currentStage, setCurrentStage] = useState<string>(STAGES[0].id);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const hasStarted = useRef(false);

  useEffect(() => {
    if (!caseId || hasStarted.current) return;
    hasStarted.current = true;

    // Simulate progress visually while actual processing happens in background
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 95) return 95;
        return p + (100 - p) * 0.05; // Asymptotic approach to 95%
      });
    }, 1000);

    let stageIdx = 0;
    const stageInterval = setInterval(() => {
      if (stageIdx < STAGES.length - 1) {
        setCompletedStages(prev => [...prev, STAGES[stageIdx].id]);
        stageIdx++;
        setCurrentStage(STAGES[stageIdx].id);
      }
    }, 2500);

    const runAnalysis = async () => {
      try {
        const res = await analyzeEvidence(caseId);
        // Process is complete
        clearInterval(interval);
        clearInterval(stageInterval);
        setProgress(100);
        setCompletedStages(STAGES.map(s => s.id));
        setCurrentStage('');
        
        setTimeout(() => {
          navigate(`/results/${caseId}`, { state: { forensicData: res } });
        }, 1500);
        
      } catch (err: any) {
        clearInterval(interval);
        clearInterval(stageInterval);
        setError(err.message || 'Pipeline processing encountered an unrecoverable error');
      }
    };

    runAnalysis();

    return () => {
      clearInterval(interval);
      clearInterval(stageInterval);
    };
  }, [caseId, navigate]);

  return (
    <div className="max-w-3xl mx-auto py-16">
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-textMain mb-2">Automated Forensic Analysis</h2>
        <p className="text-secondary font-mono text-sm">CASE ID: <span className="text-primary">{caseId}</span></p>
      </div>

      <div className="card mb-8">
        <div className="flex justify-between items-end mb-4">
          <span className="text-sm font-semibold text-textMuted uppercase tracking-wider">Overall Progress</span>
          <span className="text-2xl font-bold text-textMain">{Math.round(progress)}%</span>
        </div>
        <div className="w-full h-2 bg-surfaceHover rounded-full overflow-hidden">
          <div 
            className="h-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      <div className="space-y-4">
        {STAGES.map((stage) => {
          const isComplete = completedStages.includes(stage.id);
          const isCurrent = currentStage === stage.id && !error;
          const isPending = !isComplete && !isCurrent;
          
          return (
            <div 
              key={stage.id} 
              className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                isCurrent ? 'bg-primary/5 border-primary/30' : 'bg-surface border-border'
              }`}
            >
              <div className="flex items-center space-x-4">
                {isComplete && <CheckCircle2 className="w-6 h-6 text-success" />}
                {isCurrent && <Loader2 className="w-6 h-6 text-primary animate-spin" />}
                {isPending && <CircleDashed className="w-6 h-6 text-border" />}
                
                <span className={`font-medium ${
                  isComplete ? 'text-textMain' : isCurrent ? 'text-primary' : 'text-textMuted'
                }`}>
                  {stage.label}
                </span>
              </div>
              
              {isCurrent && stage.id === 'gemini' && (
                <span className="text-xs text-primary font-mono bg-primary/10 px-2 py-1 rounded">
                  AI ASSISTED INFERENCE RUNNING
                </span>
              )}
            </div>
          );
        })}
      </div>

      {error && (
        <div className="mt-8 bg-danger/10 border border-danger/20 rounded-lg p-6 text-danger">
          <div className="flex items-center space-x-3 mb-2">
            <AlertCircle className="w-6 h-6" />
            <h3 className="font-bold text-lg">System Halt</h3>
          </div>
          <p className="font-mono text-sm opacity-90">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 bg-danger/20 hover:bg-danger/30 text-danger px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      )}
    </div>
  );
};

export default Processing;
