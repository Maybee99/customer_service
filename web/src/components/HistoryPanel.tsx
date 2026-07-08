/**
 * HistoryPanel — full-page conversation history browser.
 *
 * Uses real API data (Conversation[]) instead of the old mock data.
 * Supports search, delete, and navigate-to-conversation.
 */

import React, { useState } from 'react';
import { motion } from 'motion/react';
import {
  Search,
  MessageSquare,
  Trash2,
  X,
  Loader2,
  Clock,
} from 'lucide-react';
import { ScreenType, Conversation } from '../types';
import Header from './Header';

interface HistoryPanelProps {
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
  conversations: Conversation[];
  loading: boolean;
  onSelectConversation: (conv: Conversation) => void;
  onDeleteConversation: (id: number) => void;
}

function formatTime(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin}分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}小时前`;
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay < 7) return `${diffDay}天前`;
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

export default function HistoryPanel({
  onNavigate,
  conversations,
  loading,
  onSelectConversation,
  onDeleteConversation,
}: HistoryPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Client-side search filter
  const filtered = conversations.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.title || '').toLowerCase().includes(q) ||
      (c.preview || '').toLowerCase().includes(q)
    );
  });

  const handleCardClick = (conv: Conversation) => {
    onSelectConversation(conv);
  };

  const handleDeleteClick = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setDeletingId(id);
  };

  const confirmDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    onDeleteConversation(id);
    setDeletingId(null);
  };

  const cancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingId(null);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] overflow-hidden text-[#1E293B]">
      <Header activeScreen={ScreenType.HISTORY} onNavigate={onNavigate} titleOverride="对话" />

      <div className="flex-1 overflow-y-auto p-6 md:p-8 no-scrollbar">
        <div className="max-w-[1000px] w-full mx-auto flex flex-col h-full gap-6">

          {/* Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <h2 className="text-xl font-bold text-[#0F172A]">对话管理</h2>
            <span className="text-xs text-[#94A3B8] font-semibold">
              共 {conversations.length} 条对话记录
            </span>
          </div>

          {/* Search */}
          <div className="relative w-full">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索对话标题或内容..."
              className="w-full pl-12 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#3B82F6]/20 focus:border-[#3B82F6] transition-all text-sm text-[#1E293B] placeholder-slate-400 shadow-sm"
            />
          </div>

          {/* Content */}
          <div className="flex-1 space-y-3">
            {/* Loading state */}
            {loading && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-[#3B82F6] animate-spin" />
                <span className="ml-3 text-sm text-[#94A3B8]">加载对话记录...</span>
              </div>
            )}

            {/* Empty state (not loading, no conversations at all) */}
            {!loading && conversations.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-[#94A3B8]">
                <MessageSquare className="w-12 h-12 mb-4 opacity-30" />
                <p className="text-sm font-semibold mb-1">暂无对话记录</p>
                <p className="text-xs">开始新对话后，记录将显示在这里</p>
              </div>
            )}

            {/* Empty search results */}
            {!loading && conversations.length > 0 && filtered.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-[#94A3B8]">
                <Search className="w-12 h-12 mb-4 opacity-30" />
                <p className="text-sm font-semibold mb-1">未找到匹配的对话</p>
                <p className="text-xs">尝试其他搜索关键词</p>
              </div>
            )}

            {/* Conversation cards */}
            {filtered.map((conv) => (
              <motion.div
                key={conv.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                onClick={() => handleCardClick(conv)}
                className="group flex items-start gap-4 p-5 bg-white border border-[#E2E8F0] hover:border-[#3B82F6]/30 rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer duration-200 relative"
              >
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-[#EFF6FF] text-[#3B82F6] shrink-0 flex items-center justify-center">
                  <MessageSquare className="w-6 h-6" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-semibold text-base text-[#1E293B] truncate pr-8 group-hover:text-[#2563EB] transition-colors">
                      {conv.title || '新对话'}
                    </h3>
                    <span className="text-xs text-[#94A3B8] shrink-0 font-medium flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(conv.updated_at)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 line-clamp-1 mb-2 font-medium">
                    {conv.preview || '（空对话）'}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#F1F5F9] text-[#475569]">
                      {conv.message_count || 0} 条消息
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      conv.status === 'active'
                        ? 'bg-green-50 text-green-600'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      {conv.status === 'active' ? '进行中' : '已关闭'}
                    </span>
                  </div>
                </div>

                {/* Delete — hover reveal or confirm */}
                {deletingId === conv.id ? (
                  <div className="absolute right-3 top-3 flex items-center gap-2 bg-white rounded-lg shadow-md border border-[#E2E8F0] px-3 py-2 z-10">
                    <span className="text-[11px] text-red-500 font-semibold whitespace-nowrap">确认删除?</span>
                    <button
                      onClick={(e) => confirmDelete(e, conv.id)}
                      className="px-2 py-0.5 bg-red-500 hover:bg-red-600 text-white text-[10px] font-bold rounded cursor-pointer"
                    >
                      删除
                    </button>
                    <button
                      onClick={cancelDelete}
                      className="p-0.5 hover:bg-slate-100 rounded text-slate-400 cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={(e) => handleDeleteClick(e, conv.id)}
                    className="absolute right-3 top-3 opacity-0 group-hover:opacity-100 p-2 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-all cursor-pointer"
                    title="删除对话"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
