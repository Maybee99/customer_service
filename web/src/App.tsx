/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { ScreenType } from './types';
import Sidebar from './components/Sidebar';
import MainChat from './components/MainChat';
import HistoryPanel from './components/HistoryPanel';
import KnowledgeBase from './components/KnowledgeBase';
import SettingsPanel from './components/SettingsPanel';

type TransitionDirection = 'push' | 'push_back' | 'none';

export default function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenType>(ScreenType.MAIN_CHAT);
  const [transitionDirection, setTransitionDirection] = useState<TransitionDirection>('none');

  const handleNavigate = (screen: ScreenType, transitionType: TransitionDirection) => {
    setTransitionDirection(transitionType);
    setActiveScreen(screen);
  };

  // Select variants based on transition type
  const getVariants = () => {
    return {
      enter: (dir: TransitionDirection) => {
        if (dir === 'push') return { x: '5%', opacity: 0 };
        if (dir === 'push_back') return { x: '-5%', opacity: 0 };
        return { opacity: 0 };
      },
      center: {
        x: 0,
        opacity: 1,
        transition: { duration: 0.3, ease: 'easeOut' }
      },
      exit: (dir: TransitionDirection) => {
        if (dir === 'push') return { x: '-5%', opacity: 0, transition: { duration: 0.2 } };
        if (dir === 'push_back') return { x: '5%', opacity: 0, transition: { duration: 0.2 } };
        return { opacity: 0, transition: { duration: 0.15 } };
      }
    };
  };

  const renderActiveScreen = () => {
    switch (activeScreen) {
      case ScreenType.MAIN_CHAT:
        return <MainChat onNavigate={handleNavigate} />;
      case ScreenType.HISTORY:
        return <HistoryPanel onNavigate={handleNavigate} />;
      case ScreenType.KNOWLEDGE:
        return <KnowledgeBase onNavigate={handleNavigate} />;
      case ScreenType.SETTINGS:
        return <SettingsPanel onNavigate={handleNavigate} />;
      default:
        return <MainChat onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#faf8ff] text-[#131b2e] font-sans antialiased">
      {/* Left Sidebar - dynamically responsive lists inside */}
      <Sidebar activeScreen={activeScreen} onNavigate={handleNavigate} />

      {/* Right Content Area with Framer Motion transitions */}
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

