import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import ReactMarkdown from 'react-markdown';
import { PlusCircle, ArrowUp, FileText, Lightbulb, Search, CheckCircle, AlertCircle, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { Message, ScreenType, StepEvent } from '../types';
import Header from './Header';

interface MainChatProps {
  messages: Message[];
  thinkingSteps: StepEvent[];
  isStreaming: boolean;
  onSend: (question: string) => void;
  onNewChat: () => void;
  onNavigate: (screen: ScreenType, t: 'none' | 'push' | 'push_back') => void;
}

function StepIcon({ type }: { type: string }) {
  switch (type) {
    case 'thinking': return <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0" />;
    case 'tool': return <Search className="w-3.5 h-3.5 text-blue-500 shrink-0" />;
    case 'result': return <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0" />;
    case 'reflect': return <AlertCircle className="w-3.5 h-3.5 text-purple-500 shrink-0" />;
    default: return <Lightbulb className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
  }
}

export default function MainChat({ messages, thinkingSteps, isStreaming, onSend, onNewChat, onNavigate }: MainChatProps) {
  const [inputValue, setInputValue] = useState('');
  const [thinkingExpanded, setThinkingExpanded] = useState(true);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinkingSteps, isStreaming]);

  // Auto-collapse thinking when answer content starts streaming
  const lastAiMsg = [...messages].reverse().find(m => m.sender === 'ai');
  const hasAnswerContent = lastAiMsg && lastAiMsg.content.length > 0;
  const hasThinking = thinkingSteps.length > 0;

  useEffect(() => {
    if (hasAnswerContent && hasThinking) {
      setThinkingExpanded(false);
    }
  }, [hasAnswerContent, hasThinking]);

  const handleSend = () => {
    if (!inputValue.trim() || isStreaming) return;
    onSend(inputValue);
    setInputValue('');
    setThinkingExpanded(true); // Reset for new message
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] relative overflow-hidden text-[#1E293B]">
      <Header activeScreen={ScreenType.MAIN_CHAT} onNavigate={onNavigate} titleOverride="智能客服" />

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6 no-scrollbar">
        <div className="max-w-[800px] mx-auto flex flex-col space-y-6">

          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center py-20 text-[#94A3B8]">
              <Lightbulb className="w-12 h-12 mb-4 opacity-50" />
              <p className="text-lg font-bold mb-1">有什么可以帮您？</p>
              <p className="text-sm">输入您的问题，开始智能对话</p>
            </div>
          )}

          {messages.map((msg, index) => {
            const isUser = msg.sender === 'user';
            const isLastAi = !isUser && index === messages.length - 1;
            const showThinkingForThis = isLastAi && thinkingSteps.length > 0;

            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
              >
                <div className={`p-4 rounded-xl shadow-sm ${
                  isUser
                    ? 'bg-[#3B82F6] text-white max-w-[80%] rounded-br-sm shadow-blue-500/10'
                    : 'bg-white text-[#1E293B] border border-[#E2E8F0] max-w-[85%] rounded-bl-sm shadow-sm'
                }`}>
                  {/* Thinking section — INSIDE the AI bubble */}
                  {showThinkingForThis && (
                    <div className="mb-3 border border-[#F1F5F9] rounded-lg overflow-hidden bg-[#F8FAFC]">
                      <button
                        onClick={() => setThinkingExpanded(!thinkingExpanded)}
                        className="w-full flex items-center justify-between px-3 py-2 text-[11px] font-bold text-[#64748B] hover:bg-[#F1F5F9] transition-colors cursor-pointer"
                      >
                        <span className="flex items-center gap-1.5">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                          思考过程
                          {isStreaming && !hasAnswerContent && (
                            <Loader2 className="w-3 h-3 text-amber-500 animate-spin" />
                          )}
                          {isStreaming && hasAnswerContent && (
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                          )}
                        </span>
                        {thinkingExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      </button>
                      <AnimatePresence>
                        {thinkingExpanded && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="px-3 py-2 space-y-1.5 border-t border-[#F1F5F9]">
                              {thinkingSteps.map((step, i) => (
                                <motion.div
                                  key={i}
                                  initial={{ opacity: 0, x: -8 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ duration: 0.2 }}
                                  className="flex items-start gap-1.5 text-[11px]"
                                >
                                  <StepIcon type={step.type} />
                                  <span className="text-[#475569] leading-relaxed whitespace-pre-wrap">{step.content}</span>
                                </motion.div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}

                  {/* Answer content */}
                  {msg.content ? (
                    isUser ? (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="text-sm leading-relaxed prose prose-sm max-w-none prose-headings:text-[#1E293B] prose-p:text-[#334155] prose-strong:text-[#1E293B] prose-li:text-[#334155] prose-a:text-[#3B82F6] prose-code:bg-[#F1F5F9] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-[#E11D48] prose-code:text-xs prose-code:before:content-none prose-code:after:content-none prose-pre:bg-[#1E293B] prose-pre:text-[#E2E8F0] prose-hr:border-[#E2E8F0] prose-blockquote:border-l-[#3B82F6] prose-blockquote:bg-[#F8FAFC] prose-blockquote:py-1 prose-blockquote:px-3 prose-blockquote:rounded-r-lg prose-table:border prose-table:border-[#E2E8F0] prose-th:bg-[#F8FAFC] prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2">
                        <ReactMarkdown
                          components={{
                            a: ({ href, children, ...props }) => (
                              <a
                                href={href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[#3B82F6] hover:text-[#2563EB] underline font-semibold"
                                {...props}
                              >
                                {children}
                              </a>
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )
                  ) : showThinkingForThis ? (
                    <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>正在思考中...</span>
                    </div>
                  ) : null}

                  {/* Source PDF link */}
                  {!isUser && msg.sourcePdf && (
                    <div className="mt-4 pt-3 border-t border-[#E2E8F0]">
                      <a href="#" onClick={(e) => e.preventDefault()} className="text-xs text-[#3B82F6] hover:text-[#2563EB] hover:underline font-semibold flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        查看来源：{msg.sourcePdf}
                      </a>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}

          <div ref={chatEndRef} />
        </div>
      </div>

      <footer className="w-full bg-[#F8FAFC] border-t border-[#E2E8F0] p-4 shrink-0 z-10">
        <div className="max-w-[800px] mx-auto">
          <div className="relative flex items-center gap-3 bg-white border border-[#E2E8F0] rounded-xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-[#3B82F6]/10 focus-within:border-[#3B82F6] transition-all">
            <button className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-[#3B82F6] hover:bg-slate-50 rounded-lg transition-colors cursor-pointer" onClick={onNewChat}>
              <PlusCircle className="w-5 h-5" />
            </button>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="请输入您的问题..."
              disabled={isStreaming}
              className="flex-1 bg-transparent border-none text-sm text-[#1E293B] placeholder-slate-400 outline-none focus:ring-0 focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isStreaming}
              className={`w-10 h-10 flex items-center justify-center rounded-lg transition-all cursor-pointer ${
                inputValue.trim() && !isStreaming
                  ? 'bg-[#3B82F6] hover:bg-[#2563EB] text-white active:scale-95 shadow-md shadow-blue-500/10'
                  : 'bg-slate-100 text-slate-300'
              }`}
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </div>
          <p className="text-center text-[10px] text-[#94A3B8] font-semibold mt-2">内容由 AI 生成，仅供参考。</p>
        </div>
      </footer>
    </div>
  );
}
