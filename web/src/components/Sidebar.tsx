/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { 
  Plus, 
  Search, 
  MessageSquare, 
  MoreHorizontal, 
  Sparkles,
  User
} from 'lucide-react';
import { ScreenType } from '../types';
import { 
  mainChatSidebar, 
  historySidebar, 
  knowledgeSidebar, 
  settingsSidebar,
  mainChatUser,
  historyUser,
  knowledgeUser,
  settingsUser
} from '../data';

interface SidebarProps {
  activeScreen: ScreenType;
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
}

export default function Sidebar({ activeScreen, onNavigate }: SidebarProps) {
  // Determine which list to show based on screen
  let title = 'Corporate AI';
  let subTitle = 'Enterprise Support';
  let historyTitle = '历史对话';
  let chatList = mainChatSidebar;
  let userProfile = mainChatUser;

  if (activeScreen === ScreenType.MAIN_CHAT) {
    title = 'Corporate AI';
    subTitle = 'Enterprise Support';
    historyTitle = '历史对话';
    chatList = mainChatSidebar;
    userProfile = mainChatUser;
  } else if (activeScreen === ScreenType.HISTORY) {
    title = 'Corporate AI';
    subTitle = 'Enterprise Support';
    historyTitle = '历史对话';
    chatList = historySidebar;
    userProfile = historyUser;
  } else if (activeScreen === ScreenType.KNOWLEDGE) {
    title = 'Corporate AI';
    subTitle = 'Enterprise Support';
    historyTitle = '最近对话';
    chatList = knowledgeSidebar;
    userProfile = knowledgeUser;
  } else if (activeScreen === ScreenType.SETTINGS) {
    title = 'Corporate AI';
    subTitle = 'Enterprise Support';
    historyTitle = '历史对话';
    chatList = settingsSidebar;
    userProfile = settingsUser;
  }

  // Handle New Chat click based on active screen
  const handleNewChat = () => {
    if (activeScreen === ScreenType.MAIN_CHAT) {
      onNavigate(ScreenType.MAIN_CHAT, 'none');
    } else {
      onNavigate(ScreenType.MAIN_CHAT, 'push_back');
    }
  };

  // Handle clicking a history item
  const handleHistoryItemClick = (index: number) => {
    // Special requirements:
    // Settings: nav class "custom-scrollbar" //a[1] -> HISTORY (push)
    // Knowledge Base: span contains "最近对话" /following::a[1] -> HISTORY (push)
    // Main Chat: span "历史对话" /following-sibling::a[1] -> HISTORY (push)
    if (index === 0) {
      onNavigate(ScreenType.HISTORY, 'push');
    } else {
      // Just for UX, go to main chat or stay
      onNavigate(ScreenType.MAIN_CHAT, 'none');
    }
  };

  return (
    <aside className="w-72 hidden md:flex flex-col bg-white border-r border-[#E2E8F0] h-full overflow-hidden shrink-0 z-40 transition-all duration-200">
      {/* Sidebar Header */}
      <div className="p-6 pb-2">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-9 h-9 bg-gradient-to-br from-[#3B82F6] to-[#2563EB] rounded-lg flex items-center justify-center text-white font-bold">
            <Sparkles className="w-4.5 h-4.5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-[#0F172A] tracking-tight">{title}</h1>
            <p className="text-[10px] text-[#94A3B8] font-bold tracking-wider uppercase">{subTitle}</p>
          </div>
        </div>

        {/* New Chat Button */}
        <button 
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 bg-[#3B82F6] hover:bg-[#2563EB] text-white py-3 rounded-lg font-semibold text-sm transition-all active:scale-[0.98] shadow-md shadow-blue-500/20 cursor-pointer"
        >
          <Plus className="w-4.5 h-4.5" />
          新建对话
        </button>

        {/* History Title bar */}
        <div className="flex items-center justify-between mt-6 mb-2 px-2">
          {activeScreen === ScreenType.KNOWLEDGE ? (
            <span className="text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider">最近对话</span>
          ) : activeScreen === ScreenType.MAIN_CHAT ? (
            <span className="text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider">历史对话</span>
          ) : (
            <span className="text-[11px] font-semibold text-[#94A3B8] uppercase tracking-wider">历史对话</span>
          )}
          <button className="p-1 hover:bg-[#F8FAFC] rounded text-[#94A3B8]">
            <Search className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* History Chat List */}
      {/* We add class "custom-scrollbar" exactly as settings spec asks for `//nav[contains(@class, 'custom-scrollbar')]//a[1]` */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar no-scrollbar pb-4">
        {chatList.map((chat, idx) => {
          const isActive = chat.active || (activeScreen === ScreenType.MAIN_CHAT && idx === 0);
          return (
            <a
              key={chat.id}
              href="#"
              onClick={(e) => {
                e.preventDefault();
                handleHistoryItemClick(idx);
              }}
              className={`flex flex-col gap-1 px-4 py-3 rounded-lg transition-all duration-200 group border-l-2 ${
                isActive 
                  ? 'bg-[#EFF6FF] border-[#3B82F6] text-[#2563EB] font-semibold' 
                  : 'border-transparent hover:bg-[#F8FAFC] text-[#475569]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-sm truncate font-medium ${isActive ? 'text-[#2563EB]' : 'text-[#1E293B]'}`}>
                  {chat.title}
                </span>
                <span className="text-[10px] text-slate-400 shrink-0">{chat.time}</span>
              </div>
              <p className="text-xs text-slate-400 truncate font-normal">{chat.preview}</p>
            </a>
          );
        })}
      </nav>

      {/* User Profile Section at Bottom */}
      <div className="p-4 border-t border-[#F1F5F9] bg-white mt-auto">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-[#F8FAFC] cursor-pointer transition-colors">
          {userProfile.avatarUrl ? (
            <img 
              src={userProfile.avatarUrl} 
              alt={userProfile.name} 
              referrerPolicy="no-referrer"
              className="w-10 h-10 rounded-full object-cover border border-[#E2E8F0]" 
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-[#F1F5F9] border border-[#E2E8F0] flex items-center justify-center text-[#64748B] font-bold">
              {userProfile.name === 'User Profile' ? 'JD' : userProfile.name.substring(0, 2)}
            </div>
          )}
          <div className="overflow-hidden flex-1">
            <p className="font-semibold text-sm text-[#1E293B] truncate">{userProfile.name}</p>
            <p className="text-xs text-slate-400 truncate">
              {userProfile.role}
            </p>
          </div>
          <MoreHorizontal className="w-4 h-4 text-slate-400 hover:text-[#1E293B]" />
        </div>
      </div>
    </aside>
  );
}
