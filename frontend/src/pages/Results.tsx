import { useState } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { Shield, Settings, Eye, Zap, FileText, CheckCircle2, XCircle } from 'lucide-react';
import Graph from '../components/Graph';

const Results = () => {
  const { caseId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const data = location.state?.forensicData;
  const [activeTab, setActiveTab] = useState('technical');

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <p className="text-secondary mb-4">No analysis data found for this case.</p>
        <button onClick={() => navigate('/')} className="btn-primary">Return to Dashboard</button>
      </div>
    );
  }

  const { privacy, enf, corneal, gemini, legal_report } = data;
  const isAuthentic = legal_report.findings?.is_authentic;

  return (
    <div className="max-w-6xl mx-auto py-8">
      {/* Top Hero Card */}
      <div className="card mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
          <div>
            <h2 className="text-2xl font-bold text-textMain mb-1">Investigation Results</h2>
            <p className="text-secondary font-mono text-sm mb-4">CASE ID: <span className="text-primary">{caseId}</span></p>
            
            <div className="flex space-x-6 mt-4">
              <div className="flex items-center space-x-2">
                <Settings className="w-5 h-5 text-secondary" />
                <span className="text-sm text-secondary uppercase">Processing Time:</span>
                <span className="text-textMain font-medium font-mono">
                  {(privacy.processing_time + enf.processing_time + corneal.processing_time + gemini.processing_time + legal_report.processing_time).toFixed(2)}s
                </span>
              </div>
            </div>
          </div>
          
          <div className={`mt-6 md:mt-0 px-6 py-4 rounded-lg border-2 ${isAuthentic ? 'bg-success/10 border-success text-success' : 'bg-danger/10 border-danger text-danger'}`}>
            <div className="flex items-center space-x-3 mb-1">
              {isAuthentic ? <CheckCircle2 className="w-8 h-8" /> : <XCircle className="w-8 h-8" />}
              <h3 className="text-xl font-bold">{legal_report.findings?.verdict_badge}</h3>
            </div>
            <p className="text-sm opacity-90 ml-11">Determined via strict multi-signal technical forensics.</p>
          </div>
        </div>
      </div>

      {/* Tabbed Navigation */}
      <div className="flex space-x-1 border-b border-border mb-8">
        <button 
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === 'technical' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-secondary hover:text-textMain'}`}
          onClick={() => setActiveTab('technical')}
        >
          Technical Forensics
        </button>
        <button 
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === 'intelligence' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-secondary hover:text-textMain'}`}
          onClick={() => setActiveTab('intelligence')}
        >
          Environmental Intelligence
        </button>
        <button 
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === 'report' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-secondary hover:text-textMain'}`}
          onClick={() => setActiveTab('report')}
        >
          Legal Report
        </button>
      </div>

      {/* Tab Content */}
      <div className="min-h-[500px]">
        {activeTab === 'technical' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center space-x-3 mb-6">
                <Shield className="w-6 h-6 text-primary" />
                <h3 className="text-lg font-bold text-textMain">Agentic Privacy Shield</h3>
              </div>
              <p className="text-sm text-secondary mb-4">Protects investigator mental health by redacting human subjects while preserving environmental context.</p>
              <div className="metric-card mb-4">
                <div className="metric-label">Status</div>
                <div className="metric-value text-success">ACTIVE</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Human Subjects Redacted</div>
                <div className="metric-value">{privacy.findings?.count || 0}</div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center space-x-3 mb-6">
                <Zap className="w-6 h-6 text-primary" />
                <h3 className="text-lg font-bold text-textMain">ENF Physics Engine</h3>
              </div>
              <p className="text-sm text-secondary mb-4">Electrical Network Frequency (50 Hz) detection from luminance oscillations.</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="metric-card">
                  <div className="metric-label">Grid Verdict</div>
                  <div className={`metric-value ${enf.findings?.is_authentic ? 'text-success' : 'text-danger'}`}>
                    {enf.findings?.verdict_text || 'UNAVAILABLE'}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Peak/Noise Ratio</div>
                  <div className="metric-value">{enf.findings?.enf_ratio?.toFixed(2) || 'N/A'}</div>
                </div>
              </div>
            </div>

            <div className="card md:col-span-2">
              <div className="flex items-center space-x-3 mb-6">
                <Eye className="w-6 h-6 text-primary" />
                <h3 className="text-lg font-bold text-textMain">Corneal Specular Topology</h3>
              </div>
              <p className="text-sm text-secondary mb-4">Analyzes reflection symmetry to detect synthetic generative anomalies.</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="metric-card">
                  <div className="metric-label">Verdict</div>
                  <div className={`metric-value ${corneal.findings?.is_authentic ? 'text-success' : 'text-danger'}`}>
                    {corneal.findings?.verdict_text || 'UNAVAILABLE'}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Symmetry Score</div>
                  <div className="metric-value">{corneal.findings?.symmetry_score?.toFixed(1) || '0.0'}%</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'intelligence' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-bold text-textMain mb-2">Visuo-Acoustic Knowledge Graph</h3>
              <p className="text-sm text-secondary mb-6">Interactive mapping of extracted environmental entities strictly derived from the active evidence.</p>
              <Graph caseId={caseId!} />
            </div>

            <div className="card">
              <h3 className="text-lg font-bold text-textMain mb-2">Semantic Scene Analysis (Gemini)</h3>
              <p className="text-sm text-secondary mb-6">AI-assisted interpretation of the preserved background environment.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-bold text-textMuted uppercase mb-3">Extracted Objects</h4>
                  <div className="flex flex-wrap gap-2">
                    {gemini.findings?.environmental_objects?.map((obj: any, idx: number) => (
                      <span key={idx} className="bg-surfaceHover border border-border px-3 py-1 rounded text-sm text-textMain">
                        {obj.entity || obj}
                      </span>
                    )) || <span className="text-secondary text-sm">No objects detected.</span>}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-textMuted uppercase mb-3">Scene Context</h4>
                  <div className="bg-background border border-border rounded p-4 text-textMain text-sm leading-relaxed">
                    <strong>Type:</strong> {gemini.findings?.scene_type || 'Unknown'}<br/><br/>
                    <strong>Summary:</strong> {gemini.findings?.context_summary || 'No semantic summary available.'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'report' && (
          <div className="card flex flex-col items-center justify-center py-16">
            <FileText className="w-16 h-16 text-secondary mb-4" />
            <h3 className="text-xl font-bold text-textMain mb-2">Court-Admissible Legal Docket</h3>
            <p className="text-secondary max-w-lg text-center mb-8">
              Generate a printable BSA 2023 compliant statutory declaration summarizing all deterministic findings and metadata.
            </p>
            <button 
              onClick={() => navigate(`/report/${caseId}`)}
              className="btn-primary flex items-center space-x-2"
            >
              <FileText className="w-4 h-4" />
              <span>View Full Report</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Results;
