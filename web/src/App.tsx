import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { ScreenType, Message, StepEvent, Conversation } from './types';
import Sidebar from './components/Sidebar';
import MainChat from './components/MainChat';
import HistoryPanel from './components/HistoryPanel';
import KnowledgeBase from './components/KnowledgeBase';
import SettingsPanel from './components/SettingsPanel';
import { sendChatMessageStream, fetchConversations, fetchConversationDetail, deleteConversation } from './services/api';

type TransitionDirection = 'push' | 'push_back' | 'none';

let msgIdCounter = 0;
function nextId(prefix: string) { return `${prefix}_${Date.now()}_${++msgIdCounter}`; }
function genSessionId() { return 'sess_' + crypto.randomUUID().slice(0, 8); }

export default function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenType>(ScreenType.MAIN_CHAT);
  const [transitionDirection, setTransitionDirection] = useState<TransitionDirection>('none');
  const [currentSessionId, setCurrentSessionId] = useState(genSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [thinkingSteps, setThinkingSteps] = useState<StepEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [convLoading, setConvLoading] = useState(false);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const userId = 'u1';
  const userName = '测试用户';

  const loadConversations = useCallback(() => {
    setConvLoading(true);
    fetchConversations(userId).then(data => {
      if (data?.conversations) setConversations(data.conversations);
    }).catch(() => {}).finally(() => setConvLoading(false));
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleNewChat = useCallback(() => {
    setCurrentSessionId(genSessionId());
    setMessages([]);
    setThinkingSteps([]);
    setActiveConvId(null);
    setActiveScreen(ScreenType.MAIN_CHAT);
  }, []);

  const handleSend = useCallback(async (question: string) => {
    if (!question.trim() || isStreaming) return;
    const userMsg: Message = { id: nextId('user'), sender: 'user', content: question, timestamp: '' };
    // Create an AI placeholder immediately so thinking steps have a home
    const aiPlaceholder: Message = { id: nextId('ai'), sender: 'ai', content: '', timestamp: '' };
    setMessages(prev => [...prev, userMsg, aiPlaceholder]);
    // Immediately show the first thinking step — don't wait for backend response
    setThinkingSteps([{ type: 'thinking', content: '正在分析您的问题...' }]);
    setIsStreaming(true);

    try {
      await sendChatMessageStream(
        question, currentSessionId, userId, userName,
        (step) => setThinkingSteps(prev => [...prev, step]),
        (token) => setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last && last.sender === 'ai') {
            const updated = { ...last, content: last.content + token };
            return [...prev.slice(0, -1), updated];
          }
          // Shouldn't happen since we create placeholder, but be safe
          return [...prev, { id: nextId('ai'), sender: 'ai', content: token, timestamp: '' }];
        }),
        (done) => {
          setIsStreaming(false);
          loadConversations();
        },
        (err) => {
          setMessages(prev => {
            const last = prev[prev.length - 1];
            if (last && last.sender === 'ai' && last.content === '') {
              // Replace empty placeholder with error
              const updated = { ...last, content: '抱歉，出错了: ' + err };
              return [...prev.slice(0, -1), updated];
            }
            return [...prev, { id: nextId('ai'), sender: 'ai', content: '抱歉，出错了: ' + err, timestamp: '' }];
          });
          setIsStreaming(false);
        }
      );
    } catch (e: any) {
      setIsStreaming(false);
    }
  }, [currentSessionId, isStreaming]);

  const handleSelectConversation = useCallback(async (conv: Conversation) => {
    setCurrentSessionId(conv.session_id);
    setActiveConvId(conv.id);
    setThinkingSteps([]);
    try {
      const data = await fetchConversationDetail(conv.id);
      const msgs: Message[] = (data?.messages || []).map((m: any, i: number) => ({
        id: nextId('hist'),
        sender: m.role === 'user' ? 'user' : 'ai',
        content: m.content || '',
        timestamp: '',
      }));
      setMessages(msgs);
    } catch {
      setMessages([]);
    }
    setActiveScreen(ScreenType.MAIN_CHAT);
  }, []);

  const handleDeleteConversation = useCallback(async (id: number) => {
    try {
      await deleteConversation(id);
      // If the deleted conversation was the active one, reset to new chat
      if (activeConvId === id) {
        handleNewChat();
      }
      // Refresh the list
      loadConversations();
    } catch {
      // silently ignore
    }
  }, [activeConvId, handleNewChat, loadConversations]);

  const handleNavigate = (screen: ScreenType, t: TransitionDirection) => {
    setTransitionDirection(t);
    setActiveScreen(screen);
  };

  const getVariants = () => ({
    enter: (dir: TransitionDirection) => {
      if (dir === 'push') return { x: '5%', opacity: 0 };
      if (dir === 'push_back') return { x: '-5%', opacity: 0 };
      return { opacity: 0 };
    },
    center: { x: 0, opacity: 1, transition: { duration: 0.3, ease: 'easeOut' as const } },
    exit: (dir: TransitionDirection) => {
      if (dir === 'push') return { x: '-5%', opacity: 0, transition: { duration: 0.2 } };
      if (dir === 'push_back') return { x: '5%', opacity: 0, transition: { duration: 0.2 } };
      return { opacity: 0, transition: { duration: 0.15 } };
    },
  });

  const renderActiveScreen = () => {
    switch (activeScreen) {
      case ScreenType.MAIN_CHAT:
        return <MainChat
          messages={messages}
          thinkingSteps={thinkingSteps}
          isStreaming={isStreaming}
          onSend={handleSend}
          onNewChat={handleNewChat}
          onNavigate={handleNavigate}
        />;
      case ScreenType.HISTORY:
        return <HistoryPanel
          onNavigate={handleNavigate}
          conversations={conversations}
          loading={convLoading}
          onSelectConversation={handleSelectConversation}
          onDeleteConversation={handleDeleteConversation}
        />;
      case ScreenType.KNOWLEDGE:
        return <KnowledgeBase onNavigate={handleNavigate} />;
      case ScreenType.SETTINGS:
        return <SettingsPanel onNavigate={handleNavigate} />;
      default:
        return <MainChat messages={messages} thinkingSteps={thinkingSteps} isStreaming={isStreaming} onSend={handleSend} onNewChat={handleNewChat} onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#faf8ff] text-[#131b2e] font-sans antialiased">
      <Sidebar
        activeScreen={activeScreen}
        onNavigate={handleNavigate}
        conversations={conversations}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
      />
      <main className="flex-1 h-full relative overflow-hidden flex flex-col">
        <AnimatePresence mode="wait" custom={transitionDirection}>
          <motion.div
            key={activeScreen}
            custom={transitionDirection}
            variants={getVariants()}
            initial="enter"
            animate="center"
            exit="exit"
            className="w-full h-full flex flex-col"
          >
            {renderActiveScreen()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
