/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  Paperclip, 
  Send, 
  PlusCircle, 
  Sparkles, 
  ArrowUp,
  FileText
} from 'lucide-react';
import { Message, ScreenType } from '../types';
import { initialChatMessages } from '../data';
import Header from './Header';

interface MainChatProps {
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
}

export default function MainChat({ onNavigate }: MainChatProps) {
  const [messages, setMessages] = useState<Message[]>(initialChatMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMsg: Message = {
      id: `user_${Date.now()}`,
      sender: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI typing back
    setTimeout(() => {
      setIsTyping(false);
      const aiMsg: Message = {
        id: `ai_${Date.now()}`,
        sender: 'ai',
        content: `感谢您的问题！我已经收到了关于“**${userMsg.content}**”的咨询。

为了给您提供最准确、最新的企业福利与流程信息，系统正在分析相关文件。通常该过程如下：
1. **密码修改**：您可以在企业 SSO 系统的设置模块中点击“重置密码”并根据手机验证码进行重试。
2. **请假流程**：在 OA 审批流中发起请假单，经部门经理及 HRBP 审核通过后即生效。
3. **福利手册**：请参考附件《2024年度员工手册》获取详细的带薪年假与五险一金配比标准。`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sourcePdf: '2024年度员工手册-福利篇.pdf',
      };
      setMessages((prev) => [...prev, aiMsg]);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const handleChipClick = (query: string) => {
    setInputValue(query);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] relative overflow-hidden text-[#1E293B]">
      {/* Top Navigation Header */}
      <Header activeScreen={ScreenType.MAIN_CHAT} onNavigate={onNavigate} titleOverride="对话" />

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6 no-scrollbar">
        <div className="max-w-[800px] mx-auto flex flex-col space-y-6">
          
          {/* Day Divider */}
          <div className="flex items-center gap-4 py-6">
            <div className="flex-1 h-px bg-[#E2E8F0]"></div>
            <span className="text-xs text-[#94A3B8] font-bold uppercase tracking-wider">今天</span>
            <div className="flex-1 h-px bg-[#E2E8F0]"></div>
          </div>

          {/* Render Messages */}
          {messages.map((msg, index) => {
            const isUser = msg.sender === 'user';
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
              >
                {/* Bubble Container */}
                <div 
                  className={`p-4 rounded-xl shadow-sm ${
                    isUser 
                      ? 'bg-[#3B82F6] text-white max-w-[80%] rounded-br-sm shadow-blue-500/10' 
                      : 'bg-white text-[#1E293B] border border-[#E2E8F0] max-w-[85%] rounded-bl-sm shadow-sm'
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  
                  {/* Optional File Attachment Source */}
                  {!isUser && msg.sourcePdf && (
                    <div className="mt-4 pt-3 border-t border-[#E2E8F0]">
                      <a 
                        href="#" 
                        onClick={(e) => e.preventDefault()}
                        className="text-xs text-[#3B82F6] hover:text-[#2563EB] hover:underline font-semibold flex items-center gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        查看来源：{msg.sourcePdf}
                      </a>
                    </div>
                  )}
                </div>
                {/* Timestamp */}
                <span className="text-[10px] text-[#94A3B8] px-1 font-medium">{msg.timestamp}</span>
              </motion.div>
            );
          })}

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-start"
            >
              <div className="bg-white px-4 py-3 rounded-xl flex items-center gap-1.5 shadow-sm border border-[#E2E8F0]">
                <span className="w-1.5 h-1.5 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </motion.div>
          )}

          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input / Control Panel Area */}
      <footer className="w-full bg-[#F8FAFC] border-t border-[#E2E8F0] p-4 shrink-0 z-10">
        <div className="max-w-[800px] mx-auto space-y-4">
          
          {/* Quick Action Chips */}
          <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
            <button 
              onClick={() => handleChipClick('如何修改密码？')}
              className="whitespace-nowrap px-4 py-1.5 rounded-full border border-[#E2E8F0] bg-white text-[#475569] text-xs font-semibold hover:bg-[#EFF6FF] hover:text-[#2563EB] hover:border-[#3B82F6] transition-all cursor-pointer"
            >
              如何修改密码？
            </button>
            <button 
              onClick={() => handleChipClick('请假申请流程')}
              className="whitespace-nowrap px-4 py-1.5 rounded-full border border-[#E2E8F0] bg-white text-[#475569] text-xs font-semibold hover:bg-[#EFF6FF] hover:text-[#2563EB] hover:border-[#3B82F6] transition-all cursor-pointer"
            >
              请假申请流程
            </button>
            <button 
              onClick={() => handleChipClick('查看福利手册')}
              className="whitespace-nowrap px-4 py-1.5 rounded-full border border-[#E2E8F0] bg-white text-[#475569] text-xs font-semibold hover:bg-[#EFF6FF] hover:text-[#2563EB] hover:border-[#3B82F6] transition-all cursor-pointer"
            >
              查看福利手册
            </button>
          </div>

          {/* Interactive Chat Input Bar */}
          <div className="relative flex items-center gap-3 bg-white border border-[#E2E8F0] rounded-xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-[#3B82F6]/10 focus-within:border-[#3B82F6] transition-all">
            <button className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-[#3B82F6] hover:bg-slate-50 rounded-lg transition-colors cursor-pointer">
              <PlusCircle className="w-5 h-5" />
            </button>
            
            <input 
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="请输入您的问题..."
              className="flex-1 bg-transparent border-none text-sm text-[#1E293B] placeholder-slate-400 outline-none focus:ring-0 focus:outline-none"
            />

            <button 
              onClick={handleSend}
              disabled={!inputValue.trim()}
              className={`w-10 h-10 flex items-center justify-center rounded-lg transition-all cursor-pointer ${
                inputValue.trim() 
                  ? 'bg-[#3B82F6] hover:bg-[#2563EB] text-white active:scale-95 shadow-md shadow-blue-500/10' 
                  : 'bg-slate-100 text-slate-300'
              }`}
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </div>

          {/* AI Disclaimer Muted Label */}
          <p className="text-center text-[10px] text-[#94A3B8] font-semibold">
            内容由 AI 生成，仅供参考。
          </p>
        </div>
      </footer>

      {/* Atmospheric Blur Overlays */}
      <div className="absolute inset-0 -z-10 pointer-events-none opacity-20 overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[#3B82F6]/15 blur-[100px]"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] rounded-full bg-[#94A3B8]/10 blur-[80px]"></div>
      </div>
    </div>
  );
}
