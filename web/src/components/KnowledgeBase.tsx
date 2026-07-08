/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  Folder, 
  FolderPlus, 
  List, 
  Grid, 
  ChevronDown, 
  Filter, 
  FileText, 
  TableProperties, 
  Edit2, 
  Trash2, 
  ChevronLeft, 
  ChevronRight,
  Upload,
  RefreshCw,
  Search,
  BookOpen
} from 'lucide-react';
import { ScreenType, KBDocument } from '../types';
import { kbDocuments } from '../data';
import Header from './Header';

interface KnowledgeBaseProps {
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
}

export default function KnowledgeBase({ onNavigate }: KnowledgeBaseProps) {
  const [selectedCategory, setSelectedCategory] = useState('全部文档');
  const [documents, setDocuments] = useState<KBDocument[]>(kbDocuments);
  const [isUploading, setIsUploading] = useState(false);

  const handleUploadMock = () => {
    setIsUploading(true);
    setTimeout(() => {
      const newDoc: KBDocument = {
        id: `kb_doc_${Date.now()}`,
        name: '企业差旅管理及补贴细则_2024.docx',
        category: '公司规章',
        size: '1.8 MB',
        updatedAt: new Date().toISOString().replace('T', ' ').substring(0, 16),
        status: '已索引',
      };
      setDocuments((prev) => [newDoc, ...prev]);
      setIsUploading(false);
    }, 1200);
  };

  const handleDelete = (id: string) => {
    setDocuments(documents.filter((doc) => doc.id !== id));
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] overflow-hidden text-[#1E293B]">
      {/* Top App Header with global navigation tabs */}
      <Header activeScreen={ScreenType.KNOWLEDGE} onNavigate={onNavigate} titleOverride="企业知识库" />

      {/* Main Container */}
      <div className="flex-1 overflow-y-auto p-6 md:p-8 no-scrollbar">
        <div className="max-w-7xl mx-auto w-full">
          
          {/* Section Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-[#0F172A]">企业知识库</h2>
            <p className="text-sm text-slate-500">集中管理您的企业文档与 AI 训练资料</p>
          </div>

          {/* Statistics Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="p-5 bg-white border border-[#E2E8F0] rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <p className="text-xs font-bold text-[#94A3B8] mb-1">总文档数</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[#0F172A]">1,284</span>
                <span className="text-xs font-bold text-[#3B82F6]">+12%</span>
              </div>
            </div>

            <div className="p-5 bg-white border border-[#E2E8F0] rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <p className="text-xs font-bold text-[#94A3B8] mb-1">存储占用</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[#0F172A]">4.2 GB</span>
                <span className="text-xs font-semibold text-slate-400">/ 10 GB</span>
              </div>
            </div>

            <div className="p-5 bg-white border border-[#E2E8F0] rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <p className="text-xs font-bold text-[#94A3B8] mb-1">本月查询量</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[#0F172A]">45.2k</span>
                <span className="text-xs font-semibold text-red-500">-3%</span>
              </div>
            </div>

            {/* Sync Status Card with spin effect */}
            <div className="p-5 bg-[#3B82F6] text-white rounded-xl shadow-sm relative overflow-hidden">
              <div className="relative z-10">
                <p className="text-xs opacity-80 mb-1 font-semibold">同步状态</p>
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span className="text-base font-bold">正在索引...</span>
                </div>
                <p className="text-[10px] mt-2 opacity-70 font-medium">上次更新：2分钟前</p>
              </div>
              {/* background vector effect */}
              <div className="absolute top-[-20%] right-[-20%] w-32 h-32 rounded-full bg-white/10 blur-xl"></div>
            </div>
          </div>

          {/* Categories and List Layout Container */}
          <div className="flex flex-col lg:flex-row gap-8">
            
            {/* Left sidebar: categories selection */}
            <div className="w-full lg:w-64 flex-shrink-0">
              <h3 className="text-[11px] font-bold text-[#94A3B8] uppercase tracking-wider mb-4 px-2">文档分类</h3>
              <div className="space-y-1">
                <button 
                  onClick={() => setSelectedCategory('全部文档')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                    selectedCategory === '全部文档'
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#475569] hover:bg-[#F8FAFC]'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Folder className="w-4 h-4" />
                    全部文档
                  </span>
                  <span className="text-xs opacity-60">1284</span>
                </button>

                <button 
                  onClick={() => setSelectedCategory('公司规章')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                    selectedCategory === '公司规章'
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#475569] hover:bg-[#F8FAFC]'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4" />
                    公司规章
                  </span>
                  <span className="text-xs opacity-60">42</span>
                </button>

                <button 
                  onClick={() => setSelectedCategory('产品说明')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                    selectedCategory === '产品说明'
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#475569] hover:bg-[#F8FAFC]'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    产品说明
                  </span>
                  <span className="text-xs opacity-60">512</span>
                </button>

                <button 
                  onClick={() => setSelectedCategory('客服话术')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                    selectedCategory === '客服话术'
                      ? 'bg-[#EFF6FF] text-[#2563EB]'
                      : 'text-[#475569] hover:bg-[#F8FAFC]'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <FolderPlus className="w-4 h-4" />
                    客服话术
                  </span>
                  <span className="text-xs opacity-60">256</span>
                </button>

                <button 
                  onClick={handleUploadMock}
                  disabled={isUploading}
                  className="w-full flex items-center gap-2 px-3 py-2 text-[#3B82F6] hover:bg-[#EFF6FF] rounded-lg text-sm font-bold transition-colors mt-4 cursor-pointer"
                >
                  <Upload className="w-4 h-4 animate-pulse" />
                  {isUploading ? '上传中...' : '新建分类'}
                </button>
              </div>
            </div>

            {/* Right sidebar: document list card table */}
            <div className="flex-1">
              <div className="bg-white border border-[#E2E8F0] rounded-xl overflow-hidden shadow-sm">
                
                {/* Toolbar */}
                <div className="px-6 py-4 border-b border-[#E2E8F0] flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <button className="p-2 bg-[#F8FAFC] text-[#1E293B] border border-[#E2E8F0] rounded-lg cursor-pointer">
                      <List className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-slate-400 hover:bg-[#F8FAFC] rounded-lg cursor-pointer">
                      <Grid className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <select className="appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg text-xs font-semibold py-2 pl-3 pr-8 focus:ring-[#3B82F6]/20 transition-all outline-none cursor-pointer">
                        <option>按修改日期排序</option>
                        <option>按文件名排序</option>
                        <option>按大小排序</option>
                      </select>
                      <ChevronDown className="w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                    </div>

                    <button className="p-2 text-slate-400 hover:bg-[#F8FAFC] rounded-lg transition-colors cursor-pointer">
                      <Filter className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Data Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-[#F8FAFC]">
                      <tr>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">文件名</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">分类</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">更新时间</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0]">状态</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 border-b border-[#E2E8F0] text-right">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {documents.map((doc) => {
                        const isPdf = doc.name.endsWith('.pdf');
                        const isXls = doc.name.endsWith('.xlsx');
                        
                        return (
                          <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors group">
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded flex items-center justify-center shrink-0 ${
                                  isPdf 
                                    ? 'bg-red-50 text-red-500' 
                                    : isXls 
                                      ? 'bg-emerald-50 text-emerald-500' 
                                      : 'bg-[#EFF6FF] text-[#3B82F6]'
                                }`}>
                                  <FileText className="w-5 h-5" />
                                </div>
                                <div className="min-w-0">
                                  <p className="text-sm font-semibold text-[#1E293B] truncate group-hover:text-[#3B82F6] transition-colors">
                                    {doc.name}
                                  </p>
                                  <p className="text-xs text-[#94A3B8] font-medium">{doc.size}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="px-2.5 py-1 bg-slate-100 text-[#475569] rounded text-xs font-semibold">
                                {doc.category}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-xs font-semibold text-slate-500">
                              {doc.updatedAt}
                            </td>
                            <td className="px-6 py-4">
                              <span className="flex items-center gap-1.5 text-xs font-bold text-[#3B82F6]">
                                <span className={`w-1.5 h-1.5 rounded-full ${
                                  doc.status === '已索引' 
                                    ? 'bg-[#3B82F6] animate-pulse' 
                                    : 'bg-amber-400'
                                }`}></span>
                                {doc.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right shrink-0">
                              <div className="flex items-center justify-end gap-1">
                                <button className="p-2 text-slate-400 hover:text-[#3B82F6] rounded-full hover:bg-[#EFF6FF] transition-all cursor-pointer">
                                  <Edit2 className="w-4 h-4" />
                                </button>
                                <button 
                                  onClick={() => handleDelete(doc.id)}
                                  className="p-2 text-slate-400 hover:text-red-500 rounded-full hover:bg-red-50 transition-all cursor-pointer"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Pagination footer */}
                <div className="px-6 py-4 flex items-center justify-between border-t border-[#E2E8F0] bg-[#F8FAFC]">
                  <p className="text-xs font-semibold text-slate-500">显示 1-10 共 1,284 个文档</p>
                  
                  <div className="flex items-center gap-1">
                    <button className="p-1.5 text-slate-400 hover:bg-[#EFF6FF] rounded-lg disabled:opacity-30 cursor-pointer" disabled>
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button className="w-8 h-8 flex items-center justify-center bg-[#3B82F6] text-white rounded-lg text-xs font-bold">
                      1
                    </button>
                    <button className="w-8 h-8 flex items-center justify-center hover:bg-[#EFF6FF] hover:text-[#3B82F6] text-slate-700 rounded-lg text-xs font-semibold">
                      2
                    </button>
                    <button className="w-8 h-8 flex items-center justify-center hover:bg-[#EFF6FF] hover:text-[#3B82F6] text-slate-700 rounded-lg text-xs font-semibold">
                      3
                    </button>
                    <span className="px-1 text-slate-400 text-xs">...</span>
                    <button className="w-8 h-8 flex items-center justify-center hover:bg-[#EFF6FF] hover:text-[#3B82F6] text-slate-700 rounded-lg text-xs font-semibold">
                      129
                    </button>
                    <button className="p-1.5 text-slate-400 hover:bg-[#EFF6FF] hover:text-[#3B82F6] rounded-lg transition-colors cursor-pointer">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>

              </div>
            </div>

          </div>

        </div>
      </div>

      {/* Floating Action Button for smaller layouts */}
      <button 
        onClick={handleUploadMock}
        className="fixed bottom-8 right-8 w-14 h-14 bg-[#3B82F6] text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-105 active:scale-95 transition-transform md:hidden z-50 cursor-pointer"
      >
        <Upload className="w-6 h-6" />
      </button>
    </div>
  );
}
