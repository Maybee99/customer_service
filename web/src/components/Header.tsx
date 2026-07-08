/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Headphones, MoreVertical, Menu, Bell, HelpCircle } from 'lucide-react';
import { ScreenType } from '../types';

interface HeaderProps {
  activeScreen: ScreenType;
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
  titleOverride?: string;
}

export default function Header({ activeScreen, onNavigate, titleOverride }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 flex justify-between items-center w-full px-6 h-16 bg-white/90 backdrop-blur-md border-b border-[#E2E8F0] shadow-sm shrink-0">
      <div className="flex items-center gap-8">
        <div className="flex items-center gap-4">
          <button className="md:hidden text-[#475569] hover:text-[#0F172A]">
            <Menu className="w-5 h-5" />
          </button>
          <span className="text-base font-bold text-[#0F172A]">
            {titleOverride || (activeScreen === ScreenType.MAIN_CHAT ? '对话' : activeScreen === ScreenType.SETTINGS ? 'AI 智能客服' : activeScreen === ScreenType.KNOWLEDGE ? '企业知识库' : '对话')}
          </span>
        </div>

        {/* Navigation Tabs - wrapped in a <nav> for easy xpath detection */}
        <nav className="hidden md:flex items-center gap-1">
          <button 
            onClick={() => onNavigate(ScreenType.MAIN_CHAT, 'none')} 
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeScreen === ScreenType.MAIN_CHAT 
                ? 'text-[#2563EB] bg-[#EFF6FF] font-bold' 
                : 'text-[#475569] hover:bg-[#F8FAFC]'
            }`}
          >
            <span>对话</span>
          </button>
          
          <button 
            onClick={() => onNavigate(ScreenType.KNOWLEDGE, 'none')} 
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeScreen === ScreenType.KNOWLEDGE 
                ? 'text-[#2563EB] bg-[#EFF6FF] font-bold' 
                : 'text-[#475569] hover:bg-[#F8FAFC]'
            }`}
          >
            <span>知识库</span>
          </button>

          <button 
            onClick={() => onNavigate(ScreenType.SETTINGS, 'none')} 
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeScreen === ScreenType.SETTINGS 
                ? 'text-[#2563EB] bg-[#EFF6FF] font-bold' 
                : 'text-[#475569] hover:bg-[#F8FAFC]'
            }`}
          >
            <span>设置</span>
          </button>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {/* Status Badge from Design HTML */}
        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-[#10B981] bg-[#EFFDF5] px-3 py-1.5 rounded-full border border-[#D1FAE5]">
          <span className="w-1.5 h-1.5 bg-[#10B981] rounded-full animate-pulse"></span>
          AI 助手在线
        </div>

        <button className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#3B82F6]/20 text-[#3B82F6] font-semibold text-xs hover:bg-[#EFF6FF] active:scale-95 transition-all cursor-pointer">
          <Headphones className="w-4 h-4" />
          转人工
        </button>
        
        {activeScreen === ScreenType.SETTINGS ? (
          <button className="p-2 text-slate-400 hover:bg-[#F8FAFC] rounded-full transition-colors active:scale-95">
            <HelpCircle className="w-5 h-5" />
          </button>
        ) : (
          <button className="p-2 text-slate-400 hover:bg-[#F8FAFC] rounded-full transition-colors active:scale-95">
            <Bell className="w-5 h-5" />
          </button>
        )}

        <button className="w-10 h-10 flex items-center justify-center rounded-full text-slate-400 hover:bg-[#F8FAFC] active:scale-95 transition-all">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
