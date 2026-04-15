"use client";

import { useState, useRef } from "react";
import { UploadCloud, CheckCircle2, FileText, X, AlertCircle } from "lucide-react";

export default function UploadPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setProgress(0);
    
    // Set file immediately to be used in UI state
    setUploadedFile(file.name);

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          return 100;
        }
        return prev + 15;
      });
    }, 200);
  };
  const removeFile = () => {
    setUploadedFile(null);
    setProgress(0);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Upload Form 16</h1>
        <p className="text-slate-500">Drag and drop your Form 16 PDF or image to get started with AI tax mapping.</p>
      </div>

      {!uploadedFile && !isUploading && (
        <label 
          className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center hover:border-primary/50 hover:bg-primary/5 transition-smooth cursor-pointer group"
        >
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef}
            accept=".pdf,image/png,image/jpeg,image/jpg"
            onChange={handleFileUpload}
          />
          <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-6 group-hover:bg-white group-hover:scale-110 transition-smooth shadow-sm">
            <UploadCloud className="w-8 h-8 text-slate-400 group-hover:text-primary transition-smooth" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">Drag files here or click below</h3>
          <p className="text-sm text-slate-500 mb-8 max-w-sm">
            Acceptable formats: PDF or image files (PDF, PNG, JPG, JPEG) up to 25MB.
          </p>
          <div className="bg-primary hover:bg-primary-dark text-white px-8 py-3 rounded-xl font-medium shadow-sm shadow-primary/30 transition-smooth">
            Select Files
          </div>
        </label>
      )}

      {isUploading && (
        <div className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-primary" />
            Uploading your document...
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm font-medium">
              <span className="text-slate-600 flex items-center gap-2">
                <FileText className="w-4 h-4" /> {uploadedFile || 'document'}
              </span>
              <span className="text-primary">{progress}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
              <div 
                className="bg-primary h-2.5 rounded-full transition-all duration-300 ease-out relative"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {uploadedFile && (
        <div className="bg-white border border-emerald-100 rounded-2xl p-8 shadow-sm">
          <div className="flex items-start justify-between mb-8">
            <div className="flex gap-4">
               <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center border border-emerald-100 shrink-0">
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
               </div>
               <div>
                 <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                   Upload Successful
                 </h3>
                 <p className="text-sm text-slate-500 mt-1">
                   {uploadedFile} • 1.2 MB
                 </p>
               </div>
            </div>
            <button 
              onClick={removeFile}
              className="p-2 hover:bg-slate-100 rounded-full text-slate-400 hover:text-slate-600 transition-smooth"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="bg-slate-50 border border-slate-100 rounded-xl p-6">
            <h4 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-primary" />
              Extracted Preview
            </h4>
            <div className="grid grid-cols-2 text-sm gap-y-4">
               <div>
                  <span className="text-slate-500 block mb-1 text-xs uppercase tracking-wider font-semibold">Employer Name</span>
                  <span className="font-semibold text-slate-800">Acme Corp Ltd.</span>
               </div>
               <div>
                  <span className="text-slate-500 block mb-1 text-xs uppercase tracking-wider font-semibold">PAN</span>
                  <span className="font-semibold text-slate-800 tracking-wider">ABCDE1234F</span>
               </div>
               <div>
                  <span className="text-slate-500 block mb-1 text-xs uppercase tracking-wider font-semibold">Gross Salary</span>
                  <span className="font-semibold text-slate-800">₹ 12,80,000</span>
               </div>
               <div>
                  <span className="text-slate-500 block mb-1 text-xs uppercase tracking-wider font-semibold">Total Tax Deducted</span>
                  <span className="font-semibold text-slate-800">₹ 1,24,800</span>
               </div>
            </div>
            
            <div className="mt-6 flex justify-end">
              <button className="bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-xl font-medium shadow-sm transition-smooth text-sm">
                Proceed to Mapping →
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 text-xs text-slate-500 justify-center bg-slate-50 py-3 rounded-lg border border-slate-100">
        <ShieldCheck className="w-4 h-4 text-slate-400" />
        <strong>Privacy First:</strong> Your files are processed securely locally and never stored permanently without consent.
      </div>
    </div>
  );
}

function ShieldCheck(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}
