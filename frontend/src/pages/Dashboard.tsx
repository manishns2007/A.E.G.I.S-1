import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { uploadEvidence } from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    try {
      setIsUploading(true);
      setError(null);
      const res = await uploadEvidence(file);
      navigate(`/processing/${res.case_id}`);
    } catch (err: any) {
      setError(err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-12">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="mb-12 text-center"
      >
        <h2 className="text-3xl font-bold text-textMain mb-4 tracking-wide">DIGITAL FORENSICS HUB</h2>
        <p className="text-secondary max-w-2xl mx-auto">
          Securely upload visual and auditory evidence for automated environmental intelligence graphing and forensic authenticity verification.
        </p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`card border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center p-20 cursor-pointer relative overflow-hidden group
          ${isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:shadow-[0_0_30px_rgba(0,210,255,0.05)]'}`}
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
            <div className="w-16 h-16 border-4 border-border border-t-primary rounded-full animate-spin mb-6"></div>
            <p className="text-lg font-medium text-textMain animate-pulse">Establishing Secure Custody Chain...</p>
          </div>
        ) : (
          <>
            <UploadCloud className="w-20 h-20 text-textMuted group-hover:text-primary transition-colors mb-6" />
            <p className="text-xl font-medium text-textMain mb-2">Drag and drop digital evidence here</p>
            <p className="text-secondary mb-8">or click to browse local files</p>
            
            <div className="flex space-x-4">
              <div className="flex items-center space-x-2 bg-surfaceHover px-3 py-1.5 rounded text-sm text-secondary">
                <File className="w-4 h-4" />
                <span>Images (.jpg, .png)</span>
              </div>
              <div className="flex items-center space-x-2 bg-surfaceHover px-3 py-1.5 rounded text-sm text-secondary">
                <File className="w-4 h-4" />
                <span>Videos (.mp4, .avi)</span>
              </div>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="mt-6 bg-danger/10 border border-danger/20 rounded p-4 flex items-start space-x-3 text-danger">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}
      
      <div className="mt-16 border-t border-border pt-12">
        <h3 className="text-lg font-semibold text-textMain mb-8 text-center uppercase tracking-widest text-textMuted">Automated Pipeline Vector Sequence</h3>
        <div className="flex justify-between items-center max-w-4xl mx-auto px-4 relative">
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-border -z-10 transform -translate-y-1/2"></div>
          
          {['SHA-256 Hashing', 'Privacy Shield', 'ENF Physics', 'Vision AI', 'Knowledge Graph'].map((step, idx) => (
            <div key={idx} className="bg-surface px-4 py-2 rounded-full border border-border text-sm font-medium text-secondary">
              {step}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
