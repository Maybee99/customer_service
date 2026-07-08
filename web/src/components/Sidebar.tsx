import React, { useState } from 'react';
import { Plus, Search, MoreHorizontal, Sparkles, Trash2, X } from 'lucide-react';
import { ScreenType, Conversation } from '../types';

interface SidebarProps {
  activeScreen: ScreenType;
  onNavigate: (screen: ScreenType, t: 'none' | 'push' | 'push_back') => void;
  conversations: Conversation[];
  onSelectConversation: (conv: Conversation) => void;
  onNewChat: () => void;
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

export default function Sidebar({ activeScreen, onNavigate, conversations, onSelectConversation, onNewChat, onDeleteConversation }: SidebarProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const handleNewChat = () => {
    onNewChat();
    if (activeScreen !== ScreenType.MAIN_CHAT) onNavigate(ScreenType.MAIN_CHAT, 'push_back');
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    setDeletingId(id);
  };

  const confirmDelete = (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    onDeleteConversation(id);
    setDeletingId(null);
  };

  const cancelDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDeletingId(null);
  };

  return (
    <aside className="w-72 hidden md:flex flex-col bg-white border-r border-[#E2E8F0] h-full overflow-hidden shrink-0 z-40">
      <div className="p-6 pb-2">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-9 h-9 bg-gradient-to-br from-[#3B82F6] to-[#2563EB] rounded-lg flex items-center justify-center text-white font-bold">
            <Sparkles className="w-4.5 h-4.5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-[#0F172A] tracking-tight">Corporate AI</h1>
            <p className="text-[10px] text-[#94A3B8] font-bold tracking-wider uppercase">Enterprise Support</p>
          </div>
        </div>
        <button onClick={handleNewChat} className="w-full flex items-center justify-center gap-2 bg-[#3B82F6] hover:bg-[#2563EB] text-white py-3 rounded-lg font-semibold text-sm transition-all active:scale-[0.98] shadow-md shadow-blue-500/20 cursor-pointer">
          <Plus className="w-4.5 h-4.5" />
          新建对话
        </button>
        <div className="flex items-center justify-between mt-6 mb-2 px-2">
          <span className="text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider">历史对话</span>
          <button className="p-1 hover:bg-[#F8FAFC] rounded text-[#94A3B8]"><Search className="w-4 h-4" /></button>
        </div>
      </div>
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar no-scrollbar pb-4">
        {conversations.length === 0 && (
          <p className="text-xs text-[#94A3B8] text-center py-8">暂无历史对话</p>
        )}
        {conversations.map((conv) => (
          <a
            key={conv.id}
            href="#"
            onClick={(e) => { e.preventDefault(); onSelectConversation(conv); }}
            className="flex flex-col gap-1 px-4 py-3 rounded-lg transition-all duration-200 group border-l-2 border-transparent hover:bg-[#F8FAFC] text-[#475569] relative"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm truncate font-medium text-[#1E293B]">{conv.title || '新对话'}</span>
              <span className="text-[10px] text-slate-400 shrink-0">{formatTime(conv.updated_at)}</span>
            </div>
            <p className="text-xs text-slate-400 truncate font-normal">{conv.preview}</p>
            {/* Delete button — visible on hover */}
            {deletingId === conv.id ? (
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 bg-white rounded-lg shadow-md border border-[#E2E8F0] px-2 py-1.5 z-10">
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
                onClick={(e) => handleDelete(e, conv.id)}
                className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-all cursor-pointer"
                title="删除对话"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </a>
        ))}
      </nav>
      <div className="p-4 border-t border-[#F1F5F9] bg-white mt-auto">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-[#F8FAFC] cursor-pointer transition-colors">
          <div className="w-10 h-10 rounded-full bg-[#F1F5F9] border border-[#E2E8F0] flex items-center justify-center text-[#64748B] font-bold">U</div>
          <div className="overflow-hidden flex-1">
            <p className="font-semibold text-sm text-[#1E293B] truncate">测试用户</p>
            <p className="text-xs text-slate-400 truncate">Employee ID: 0001</p>
          </div>
          <MoreHorizontal className="w-4 h-4 text-slate-400" />
        </div>
      </div>
    </aside>
  );
}
