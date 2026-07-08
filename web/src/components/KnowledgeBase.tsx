import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'motion/react';
import {
  List, Grid, ChevronDown, Filter, FileText,
  Trash2, ChevronLeft, ChevronRight, Upload, RefreshCw,
  BookOpen, AlertCircle, CheckCircle, Loader2,
} from 'lucide-react';
import { ScreenType, KnowledgeFileItem } from '../types';
import Header from './Header';
import UploadDialog from './UploadDialog';
import {
  fetchKnowledgeFiles,
  uploadKnowledgeFile,
  deleteKnowledgeFile,
  reindexKnowledgeFile,
} from '../services/api';

interface KnowledgeBaseProps {
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
}

const CATEGORIES = [
  { value: '', label: '全部分类', icon: BookOpen },
  { value: 'hr_policy', label: 'HR 政策', icon: BookOpen },
  { value: 'finance', label: '财务 / 报销', icon: FileText },
  { value: 'it_support', label: 'IT 支持', icon: FileText },
  { value: 'company_rules', label: '公司规章', icon: BookOpen },
];

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatTime(iso: string): string {
  if (!iso) return '';
  return iso.replace('T', ' ').substring(0, 16);
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'ready':
      return (
        <span className="flex items-center gap-1.5 text-xs font-bold text-green-600">
          <CheckCircle className="w-3 h-3" /> 已就绪
        </span>
      );
    case 'processing':
    case 'uploading':
      return (
        <span className="flex items-center gap-1.5 text-xs font-bold text-amber-600">
          <Loader2 className="w-3 h-3 animate-spin" /> 处理中
        </span>
      );
    case 'failed':
      return (
        <span className="flex items-center gap-1.5 text-xs font-bold text-red-500">
          <AlertCircle className="w-3 h-3" /> 失败
        </span>
      );
    default:
      return <span className="text-xs text-slate-400">{status}</span>;
  }
}

export default function KnowledgeBase({ onNavigate }: KnowledgeBaseProps) {
  const [files, setFiles] = useState<KnowledgeFileItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadFiles = useCallback(async (p: number, cat: string) => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchKnowledgeFiles({
        page: p,
        page_size: pageSize,
        category: cat || undefined,
      });
      setFiles(Array.isArray(data.files) ? data.files : []);
      setTotal(typeof data.total === 'number' ? data.total : 0);
    } catch (e: any) {
      setError(e.message || '加载失败');
      setFiles([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [pageSize]);

  // Initial load + reload on category/page change
  useEffect(() => {
    loadFiles(page, selectedCategory);
  }, [page, selectedCategory, loadFiles]);

  // Poll for processing files
  useEffect(() => {
    const hasProcessing = files.some(
      f => f.status === 'processing' || f.status === 'uploading'
    );

    if (hasProcessing && !pollingRef.current) {
      pollingRef.current = setInterval(() => {
        loadFiles(page, selectedCategory);
      }, 3000);
    } else if (!hasProcessing && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [files, page, selectedCategory, loadFiles]);

  const handleUpload = async (file: File, category: string) => {
    const result = await uploadKnowledgeFile(file, category);
    // Reload to show the new file with "processing" status
    setPage(1);
    await loadFiles(1, selectedCategory);
    // Start polling the new file's status
    let attempts = 0;
    const maxAttempts = 60; // 3 minutes max
    const poll = setInterval(async () => {
      attempts++;
      try {
        const data = await fetchKnowledgeFiles({ page: 1, page_size: 1 });
        const uploaded = data.files.find(f => f.id === result.id);
        if (!uploaded || uploaded.status === 'ready' || uploaded.status === 'failed' || attempts >= maxAttempts) {
          clearInterval(poll);
          await loadFiles(1, selectedCategory);
        }
      } catch {
        clearInterval(poll);
        await loadFiles(1, selectedCategory);
      }
    }, 2000);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`确定要删除「${name}」吗？\n该操作将同时移除所有向量数据和索引。`)) return;
    setDeleting(id);
    try {
      await deleteKnowledgeFile(id);
      await loadFiles(page, selectedCategory);
    } catch (e: any) {
      alert('删除失败: ' + (e.message || '未知错误'));
    } finally {
      setDeleting(null);
    }
  };

  const handleReindex = async (id: number) => {
    try {
      await reindexKnowledgeFile(id);
      await loadFiles(page, selectedCategory);
    } catch (e: any) {
      alert('重新索引失败: ' + (e.message || '未知错误'));
    }
  };

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat);
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const totalSize = files.reduce((sum, f) => sum + (f.file_size || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] overflow-hidden text-[#1E293B]">
      <Header activeScreen={ScreenType.KNOWLEDGE} onNavigate={onNavigate} titleOverride="企业知识库" />

      <div className="flex-1 overflow-y-auto p-6 md:p-8 no-scrollbar">
        <div className="max-w-7xl mx-auto w-full">

          {/* Section Header */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-[#0F172A]">企业知识库</h2>
              <p className="text-sm text-slate-500">集中管理文档，为 AI 客服提供知识来源</p>
            </div>
            <button
              onClick={() => setUploadOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-[#3B82F6] text-white rounded-xl text-sm font-bold hover:bg-[#2563EB] shadow-md shadow-blue-500/10 active:scale-95 transition-all cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              上传文档
            </button>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="p-5 bg-white border border-[#E2E8F0] rounded-xl shadow-sm">
              <p className="text-xs font-bold text-[#94A3B8] mb-1">总文档数</p>
              <span className="text-2xl font-bold text-[#0F172A]">{total}</span>
            </div>
            <div className="p-5 bg-white border border-[#E2E8F0] rounded-xl shadow-sm">
              <p className="text-xs font-bold text-[#94A3B8] mb-1">存储占用</p>
              <span className="text-2xl font-bold text-[#0F172A]">{formatSize(totalSize)}</span>
            </div>
            <div className="p-5 bg-white border border-[#E2E8F0] rounded-xl shadow-sm">
              <p className="text-xs font-bold text-[#94A3B8] mb-1">已就绪</p>
              <span className="text-2xl font-bold text-green-600">
                {files.filter(f => f.status === 'ready').length}
              </span>
            </div>
            <div className="p-5 bg-[#3B82F6] text-white rounded-xl shadow-sm relative overflow-hidden">
              <div className="relative z-10">
                <p className="text-xs opacity-80 mb-1 font-semibold">同步状态</p>
                <div className="flex items-center gap-2">
                  {files.some(f => f.status === 'processing') ? (
                    <><RefreshCw className="w-5 h-5 animate-spin" /><span className="text-base font-bold">索引中...</span></>
                  ) : (
                    <><CheckCircle className="w-5 h-5" /><span className="text-base font-bold">已同步</span></>
                  )}
                </div>
              </div>
              <div className="absolute top-[-20%] right-[-20%] w-32 h-32 rounded-full bg-white/10 blur-xl"></div>
            </div>
          </div>

          {/* Main layout */}
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Left sidebar: categories */}
            <div className="w-full lg:w-56 flex-shrink-0">
              <h3 className="text-[11px] font-bold text-[#94A3B8] uppercase tracking-wider mb-4 px-2">文档分类</h3>
              <div className="space-y-1">
                {CATEGORIES.map(cat => (
                  <button
                    key={cat.value}
                    onClick={() => handleCategoryChange(cat.value)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                      selectedCategory === cat.value
                        ? 'bg-[#EFF6FF] text-[#2563EB]'
                        : 'text-[#475569] hover:bg-[#F8FAFC]'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <cat.icon className="w-4 h-4" />
                      {cat.label}
                    </span>
                  </button>
                ))}
              </div>

              <button
                onClick={() => setUploadOpen(true)}
                className="w-full flex items-center gap-2 px-3 py-2.5 text-[#3B82F6] hover:bg-[#EFF6FF] rounded-lg text-sm font-bold transition-colors mt-4 cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                上传新文档
              </button>
            </div>

            {/* Right: file table */}
            <div className="flex-1">
              <div className="bg-white border border-[#E2E8F0] rounded-xl overflow-hidden shadow-sm">
                {/* Toolbar */}
                <div className="px-6 py-4 border-b border-[#E2E8F0] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button className="p-2 bg-[#F8FAFC] text-[#1E293B] border border-[#E2E8F0] rounded-lg cursor-pointer">
                      <List className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-slate-400 hover:bg-[#F8FAFC] rounded-lg cursor-pointer">
                      <Grid className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadFiles(page, selectedCategory)}
                      className="p-2 text-slate-400 hover:bg-[#F8FAFC] rounded-lg transition-colors cursor-pointer"
                      title="刷新"
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-[#F8FAFC]">
                      <tr>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">文件名</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">分类</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">大小</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">更新时间</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">状态</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0] text-right">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {loading && files.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-12 text-center">
                            <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-300 mb-3" />
                            <p className="text-sm text-slate-400">加载中...</p>
                          </td>
                        </tr>
                      ) : error ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-12 text-center">
                            <AlertCircle className="w-6 h-6 mx-auto text-red-300 mb-3" />
                            <p className="text-sm text-red-500 mb-2">{error}</p>
                            <button
                              onClick={() => loadFiles(page, selectedCategory)}
                              className="text-xs font-bold text-[#3B82F6] hover:underline"
                            >
                              点击重试
                            </button>
                          </td>
                        </tr>
                      ) : files.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-12 text-center">
                            <FileText className="w-8 h-8 mx-auto text-slate-200 mb-3" />
                            <p className="text-sm text-slate-400 mb-1">暂无文档</p>
                            <p className="text-xs text-slate-300">上传 PDF 或 Word 文档来构建知识库</p>
                          </td>
                        </tr>
                      ) : (
                        files.map(file => {
                          const isPdf = file.file_type === 'pdf';

                          return (
                            <tr key={file.id} className="hover:bg-slate-50/50 transition-colors group">
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                  <div className={`w-10 h-10 rounded flex items-center justify-center shrink-0 ${
                                    isPdf ? 'bg-red-50 text-red-500' : 'bg-blue-50 text-blue-500'
                                  }`}>
                                    <FileText className="w-5 h-5" />
                                  </div>
                                  <div className="min-w-0">
                                    <p className="text-sm font-semibold text-[#1E293B] truncate max-w-[240px] group-hover:text-[#3B82F6] transition-colors">
                                      {file.original_filename}
                                    </p>
                                    <p className="text-xs text-[#94A3B8] font-medium">
                                      {file.chunk_count > 0 ? `${file.chunk_count} 个分块` : '—'}
                                    </p>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <span className="px-2.5 py-1 bg-slate-100 text-[#475569] rounded text-xs font-semibold">
                                  {file.category || '未分类'}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-xs font-semibold text-slate-500">
                                {formatSize(file.file_size)}
                              </td>
                              <td className="px-6 py-4 text-xs font-semibold text-slate-500">
                                {formatTime(file.updated_at || file.created_at)}
                              </td>
                              <td className="px-6 py-4">
                                <StatusBadge status={file.status} />
                              </td>
                              <td className="px-6 py-4 text-right">
                                <div className="flex items-center justify-end gap-1">
                                  {file.status === 'failed' && (
                                    <button
                                      onClick={() => handleReindex(file.id)}
                                      className="px-2.5 py-1.5 text-xs font-bold text-amber-600 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
                                    >
                                      重试
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleDelete(file.id, file.original_filename)}
                                    disabled={deleting === file.id}
                                    className="p-2 text-slate-400 hover:text-red-500 rounded-full hover:bg-red-50 transition-all cursor-pointer disabled:opacity-30"
                                  >
                                    {deleting === file.id ? (
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                      <Trash2 className="w-4 h-4" />
                                    )}
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="px-6 py-4 flex items-center justify-between border-t border-[#E2E8F0] bg-[#F8FAFC]">
                    <p className="text-xs font-semibold text-slate-500">
                      共 {total} 个文档，第 {page}/{totalPages} 页
                    </p>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page <= 1}
                        className="p-1.5 text-slate-400 hover:bg-[#EFF6FF] rounded-lg disabled:opacity-30 cursor-pointer"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                        const pageNum = i + 1;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => setPage(pageNum)}
                            className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-bold ${
                              pageNum === page
                                ? 'bg-[#3B82F6] text-white'
                                : 'hover:bg-[#EFF6FF] hover:text-[#3B82F6] text-slate-700'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page >= totalPages}
                        className="p-1.5 text-slate-400 hover:bg-[#EFF6FF] rounded-lg disabled:opacity-30 cursor-pointer"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload dialog */}
      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUpload={handleUpload}
      />
    </div>
  );
}
