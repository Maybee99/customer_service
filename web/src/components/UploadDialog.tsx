import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Upload, X, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File, category: string) => Promise<number>;
}

const CATEGORIES = [
  { value: 'hr_policy', label: 'HR 政策 / 福利' },
  { value: 'finance', label: '财务 / 报销' },
  { value: 'it_support', label: 'IT 支持' },
  { value: 'company_rules', label: '公司规章' },
];

const MAX_SIZE = 50 * 1024 * 1024;

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function UploadDialog({ open, onClose, onUpload }: UploadDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState('hr_policy');
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reset = useCallback(() => {
    setFile(null);
    setCategory('hr_policy');
    setDragOver(false);
    setUploading(false);
    setError('');
  }, []);

  const handleClose = () => {
    if (uploading) return;
    reset();
    onClose();
  };

  const validateAndSetFile = (f: File | null) => {
    setError('');
    if (!f) return;
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx' && ext !== 'doc') {
      setError('仅支持 PDF (.pdf) 和 Word (.docx) 文档');
      return;
    }
    if (f.size > MAX_SIZE) {
      setError(`文件过大（${formatSize(f.size)}），最大 50 MB`);
      return;
    }
    if (f.size === 0) {
      setError('文件为空');
      return;
    }
    setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    validateAndSetFile(e.dataTransfer.files[0] || null);
  };

  const handleUpload = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setError('');
    try {
      await onUpload(file, category);
      reset();
      onClose();
    } catch (e: any) {
      setError(e.message || '上传失败');
      setUploading(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={handleClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#E2E8F0]">
              <h2 className="text-lg font-bold text-[#1E293B] flex items-center gap-2">
                <Upload className="w-5 h-5 text-[#3B82F6]" />上传文档
              </h2>
              <button onClick={handleClose} disabled={uploading}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-[#F1F5F9] transition-colors cursor-pointer disabled:opacity-30">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              <div onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)} onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                  dragOver ? 'border-[#3B82F6] bg-[#EFF6FF]'
                    : file ? 'border-green-300 bg-green-50/50'
                    : 'border-[#CBD5E1] hover:border-[#94A3B8] bg-[#F8FAFC]'
                }`}
              >
                <input ref={fileInputRef} type="file" accept=".pdf,.docx,.doc" className="hidden"
                  onChange={(e) => validateAndSetFile(e.target.files?.[0] || null)} />
                {file ? (
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle className="w-10 h-10 text-green-500" />
                    <p className="text-sm font-bold text-[#1E293B] truncate max-w-full">{file.name}</p>
                    <p className="text-xs text-slate-400">{formatSize(file.size)}</p>
                    <button onClick={(e) => { e.stopPropagation(); setFile(null); }}
                      className="text-xs text-[#3B82F6] hover:underline font-semibold mt-1">重新选择</button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <FileText className="w-10 h-10 text-slate-300" />
                    <div>
                      <p className="text-sm font-bold text-slate-500">
                        拖拽文件到此处，或<span className="text-[#3B82F6]">点击选择</span></p>
                      <p className="text-xs text-slate-400 mt-1">支持 PDF / Word (.docx)，最大 50 MB</p>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-[#64748B] mb-2">文档分类</label>
                <select value={category} onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-3 py-2.5 text-sm font-semibold text-[#1E293B] focus:ring-2 focus:ring-[#3B82F6]/20 focus:border-[#3B82F6] outline-none cursor-pointer">
                  {CATEGORIES.map(c => (<option key={c.value} value={c.value}>{c.label}</option>))}
                </select>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-xs font-semibold text-red-500 bg-red-50 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />{error}
                </div>
              )}

              <div className="flex items-center gap-3 pt-2">
                <button onClick={handleClose} disabled={uploading}
                  className="flex-1 px-4 py-2.5 text-sm font-bold text-[#64748B] bg-[#F1F5F9] hover:bg-[#E2E8F0] rounded-xl transition-colors cursor-pointer disabled:opacity-30">取消</button>
                <button onClick={handleUpload} disabled={!file || uploading}
                  className={`flex-1 px-4 py-2.5 text-sm font-bold rounded-xl transition-all cursor-pointer flex items-center justify-center gap-2 ${
                    file && !uploading ? 'bg-[#3B82F6] text-white hover:bg-[#2563EB] shadow-md shadow-blue-500/10 active:scale-[0.97]'
                      : 'bg-slate-100 text-slate-300 cursor-not-allowed'}`}>
                  {uploading ? <><Loader2 className="w-4 h-4 animate-spin" />上传中...</> : '开始上传'}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
