import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Printer } from 'lucide-react';
import axios from 'axios';

const getReportUrl = (caseId: string) => `http://localhost:8000/api/report/${caseId}`;

const Report = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const url = getReportUrl(caseId!);
        const res = await axios.get(url);
        setHtmlContent(res.data);
      } catch (err: any) {
        setError('Failed to fetch legal docket.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchReport();
  }, [caseId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <div className="p-12 text-center text-secondary">Generating Court Docket...</div>;
  if (error) return <div className="p-12 text-center text-danger">{error}</div>;

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex justify-between items-center mb-8 print:hidden">
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-secondary hover:text-primary transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Results</span>
        </button>
        
        <div className="flex space-x-4">
          <button onClick={handlePrint} className="btn-primary flex items-center space-x-2">
            <Printer className="w-4 h-4" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      <div 
        className="bg-background rounded-xl overflow-hidden shadow-2xl print:shadow-none"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    </div>
  );
};

export default Report;
