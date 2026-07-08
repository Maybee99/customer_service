/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  User, 
  Bolt, 
  Gauge, 
  Bell, 
  Palette, 
  Sun, 
  Moon, 
  AlertTriangle, 
  Save, 
  HelpCircle,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { ScreenType } from '../types';
import Header from './Header';

interface SettingsPanelProps {
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
}

export default function SettingsPanel({ onNavigate }: SettingsPanelProps) {
  const [displayName, setDisplayName] = useState('张经理');
  const [email, setEmail] = useState('zhang.manager@corporate.com');
  const [selectedModel, setSelectedModel] = useState<'gpt4' | 'gpt3'>('gpt4');
  const [desktopPush, setDesktopPush] = useState(true);
  const [highContrast, setHighContrast] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
    }, 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] overflow-hidden relative text-[#1E293B]">
      {/* Top Navigation Header */}
      <Header activeScreen={ScreenType.SETTINGS} onNavigate={onNavigate} titleOverride="AI 智能客服" />

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-6 py-8 no-scrollbar pb-24">
        <div className="max-w-[800px] mx-auto space-y-8">
          
          {/* Page Title */}
          <div>
            <h3 className="text-2xl font-bold text-[#0F172A]">偏好设置</h3>
            <p className="text-sm text-slate-500 mt-2">管理您的账户安全、模型选择及 AI 交互偏好。</p>
          </div>

          {/* Profile Section */}
          <section className="bg-white border border-[#E2E8F0] rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-[#EFF6FF] flex items-center justify-center rounded-lg text-[#3B82F6]">
                <User className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#0F172A]">基本信息</h4>
                <p className="text-xs text-slate-400 font-semibold">管理您的个人资料与公开身份。</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 ml-1">显示名称</label>
                <input 
                  type="text" 
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-2.5 text-sm text-[#1E293B] focus:ring-2 focus:ring-[#3B82F6]/20 focus:border-[#3B82F6] outline-none transition-all font-semibold"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 ml-1">电子邮箱</label>
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-4 py-2.5 text-sm text-[#1E293B] focus:ring-2 focus:ring-[#3B82F6]/20 focus:border-[#3B82F6] outline-none transition-all font-semibold"
                />
              </div>
            </div>
          </section>

          {/* AI Preferences (Bento layout cards) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Model Selection (ColSpan 2) */}
            <section className="md:col-span-2 bg-white border border-[#E2E8F0] rounded-xl p-6 shadow-sm">
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#EFF6FF] flex items-center justify-center rounded-lg text-[#3B82F6]">
                    <Bolt className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#0F172A]">默认 AI 模型</h4>
                </div>
                <span className="px-2.5 py-1 bg-[#3B82F6] text-white text-[10px] rounded-lg font-bold">推荐</span>
              </div>

              <div className="space-y-3">
                {/* GPT-4o Enterprise */}
                <div 
                  onClick={() => setSelectedModel('gpt4')}
                  className={`flex items-center justify-between p-4 border rounded-xl cursor-pointer transition-all ${
                    selectedModel === 'gpt4'
                      ? 'bg-[#EFF6FF] border-[#3B82F6]'
                      : 'bg-[#F8FAFC] border-[#E2E8F0] hover:border-[#3B82F6]/30'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      selectedModel === 'gpt4' ? 'bg-[#3B82F6] text-white' : 'bg-[#EFF6FF] text-slate-500'
                    }`}>
                      <Bolt className="w-4 h-4" />
                    </div>
                    <div>
                      <p className={`text-xs font-bold ${selectedModel === 'gpt4' ? 'text-[#2563EB]' : 'text-slate-700'}`}>GPT-4o Enterprise</p>
                      <p className="text-[10px] text-slate-400 font-semibold">针对复杂逻辑与文档 analysis 优化</p>
                    </div>
                  </div>
                  {selectedModel === 'gpt4' && <CheckCircle2 className="w-5 h-5 text-[#3B82F6]" />}
                </div>

                {/* GPT-3.5 Turbo */}
                <div 
                  onClick={() => setSelectedModel('gpt3')}
                  className={`flex items-center justify-between p-4 border rounded-xl cursor-pointer transition-all ${
                    selectedModel === 'gpt3'
                      ? 'bg-[#EFF6FF] border-[#3B82F6]'
                      : 'bg-[#F8FAFC] border-[#E2E8F0] hover:border-[#3B82F6]/30'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      selectedModel === 'gpt3' ? 'bg-[#3B82F6] text-white' : 'bg-[#EFF6FF] text-slate-500'
                    }`}>
                      <Gauge className="w-4 h-4" />
                    </div>
                    <div>
                      <p className={`text-xs font-bold ${selectedModel === 'gpt3' ? 'text-[#2563EB]' : 'text-slate-700'}`}>GPT-3.5 Turbo</p>
                      <p className="text-[10px] text-slate-400 font-semibold">极速响应，适合日常简单对话</p>
                    </div>
                  </div>
                  {selectedModel === 'gpt3' && <CheckCircle2 className="w-5 h-5 text-[#3B82F6]" />}
                </div>
              </div>
            </section>

            {/* Push Notifications Card */}
            <section className="bg-white border border-[#E2E8F0] rounded-xl p-6 shadow-sm flex flex-col justify-between">
              <div className="space-y-4">
                <div className="w-10 h-10 bg-[#F1F5F9] flex items-center justify-center rounded-lg text-slate-600">
                  <Bell className="w-5 h-5 animate-pulse" />
                </div>
                <h4 className="text-sm font-bold text-[#0F172A]">系统通知</h4>
                <p className="text-[11px] text-slate-400 leading-relaxed font-semibold">开启此项以在任务完成或 AI 有新回复时接收推送消息。</p>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-[#E2E8F0]">
                <span className="text-xs font-bold text-slate-600">实时桌面推送</span>
                <button 
                  onClick={() => setDesktopPush(!desktopPush)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    desktopPush ? 'bg-[#3B82F6]' : 'bg-slate-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      desktopPush ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </section>

          </div>

          {/* Visual Display Theme Settings */}
          <section className="bg-white border border-[#E2E8F0] rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-red-100 text-red-500 flex items-center justify-center rounded-lg">
                <Palette className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-[#0F172A]">界面与显示</h4>
            </div>

            <div className="space-y-6">
              {/* Dark mode simulation */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-700">暗黑模式</p>
                  <p className="text-[10px] text-slate-400 font-semibold">根据系统偏好自动切换外观</p>
                </div>
                <div className="flex bg-[#F8FAFC] p-1 rounded-lg border border-[#E2E8F0]">
                  <button 
                    onClick={() => setIsDarkMode(false)}
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1 cursor-pointer transition-all ${
                      !isDarkMode ? 'bg-white text-[#2563EB] shadow-sm' : 'text-slate-500'
                    }`}
                  >
                    <Sun className="w-3.5 h-3.5" />浅色
                  </button>
                  <button 
                    onClick={() => setIsDarkMode(true)}
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1 cursor-pointer transition-all ${
                      isDarkMode ? 'bg-[#0F172A] text-white shadow-sm' : 'text-slate-500'
                    }`}
                  >
                    <Moon className="w-3.5 h-3.5" />深色
                  </button>
                </div>
              </div>

              {/* High Contrast */}
              <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-700">高对比度模式</p>
                  <p className="text-[10px] text-slate-400 font-semibold">增强文本清晰度，缓解视觉疲劳</p>
                </div>
                <button 
                  onClick={() => setHighContrast(!highContrast)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    highContrast ? 'bg-[#3B82F6]' : 'bg-slate-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      highContrast ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </section>

          {/* Danger Zone */}
          <section className="border border-red-200 bg-red-50/20 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-red-100 text-red-600 rounded-lg shrink-0">
                <AlertTriangle className="w-5 h-5 animate-bounce" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-bold text-red-600">账号安全与敏感操作</h4>
                <p className="text-xs text-slate-400 font-semibold mt-1">这些操作无法撤销，请谨慎处理。</p>
                
                <div className="mt-6 flex flex-wrap gap-3">
                  <button className="px-4 py-2 border border-red-200 text-red-500 hover:bg-red-100/35 rounded-xl text-xs font-semibold active:scale-95 transition-all cursor-pointer">
                    清空所有历史对话
                  </button>
                  <button className="px-4 py-2 bg-red-500 text-white hover:bg-red-600 rounded-xl text-xs font-semibold active:scale-95 transition-all cursor-pointer">
                    注销账号
                  </button>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>

      {/* Floating Action Save Button */}
      <div className="fixed bottom-8 right-8 z-50">
        <button 
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-3 bg-[#3B82F6] hover:bg-[#2563EB] text-white rounded-full shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer"
        >
          <Save className="w-5 h-5" />
          <span className="text-xs font-bold">{isSaved ? '已保存！' : '保存更改'}</span>
        </button>
      </div>
    </div>
  );
}
