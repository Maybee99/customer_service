/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  Search, 
  Users, 
  CreditCard, 
  Cpu, 
  Star, 
  Trash2,
  Bell,
  CheckCircle,
  HelpCircle,
  MoreVertical
} from 'lucide-react';
import { ScreenType, HistoryItem } from '../types';
import { historyItems } from '../data';
import Header from './Header';

interface HistoryPanelProps {
  onNavigate: (screen: ScreenType, transitionType: 'none' | 'push' | 'push_back') => void;
}

export default function HistoryPanel({ onNavigate }: HistoryPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('全部');
  const [items, setItems] = useState<HistoryItem[]>(historyItems);

  // Filter items based on search and category
  const filteredItems = items.filter((item) => {
    const matchesSearch = 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.preview.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = selectedCategory === '全部' || item.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setItems(items.filter((item) => item.id !== id));
  };

  const handleCardClick = (item: HistoryItem) => {
    if (item.title === '入职五险一金政策咨询') {
      onNavigate(ScreenType.MAIN_CHAT, 'push_back');
    } else {
      // Go to main chat generally
      onNavigate(ScreenType.MAIN_CHAT, 'none');
    }
  };

  const categories = ['全部', '人力资源', '财务报销', '技术支持'];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F8FAFC] overflow-hidden text-[#1E293B]">
      {/* Top Header Navigation */}
      <Header activeScreen={ScreenType.HISTORY} onNavigate={onNavigate} titleOverride="对话" />

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 md:p-8 no-scrollbar">
        <div className="max-w-[1000px] w-full mx-auto flex flex-col h-full gap-6">
          
          {/* Section Header with Category Buttons */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <h2 className="text-xl font-bold text-[#0F172A]">对话管理</h2>
            
            {/* Filter Buttons */}
            <div className="flex gap-2 w-full md:w-auto overflow-x-auto no-scrollbar pb-1">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`whitespace-nowrap px-4 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                    selectedCategory === cat
                      ? 'bg-[#EFF6FF] text-[#2563EB] border-[#3B82F6]/20'
                      : 'bg-white text-slate-500 border-[#E2E8F0] hover:border-[#3B82F6]/50'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Search Input Box */}
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

          {/* History List Container */}
          <div className="flex-1 space-y-6">
            <div className="flex items-center gap-4 mb-4">
              <span className="text-xs font-bold text-[#94A3B8] uppercase tracking-wider">今天</span>
              <div className="h-px flex-1 bg-[#E2E8F0]"></div>
            </div>

            <div className="space-y-3">
              {filteredItems.length > 0 ? (
                filteredItems.map((item) => {
                  const isCurrent = item.status === '当前对话';
                  
                  // Category icon selector
                  let IconComponent = Users;
                  let iconBg = 'bg-[#EFF6FF] text-[#3B82F6]';
                  if (item.category === '财务报销') {
                    IconComponent = CreditCard;
                    iconBg = 'bg-amber-50 text-amber-500';
                  } else if (item.category === '技术支持') {
                    IconComponent = Cpu;
                    iconBg = 'bg-indigo-50 text-indigo-500';
                  }

                  return (
                    <motion.div
                      key={item.id}
                      onClick={() => handleCardClick(item)}
                      className={`history-list-item group flex items-start gap-4 p-5 bg-white border ${
                        isCurrent ? 'border-[#3B82F6]/40 shadow-sm' : 'border-[#E2E8F0] hover:border-[#3B82F6]/30'
                      } rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer duration-200`}
                    >
                      {/* Icon */}
                      <div className={`w-12 h-12 rounded-lg ${iconBg} flex-shrink-0 flex items-center justify-center`}>
                        <IconComponent className="w-6 h-6" />
                      </div>

                      {/* Content details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start mb-1">
                          <h3 className="font-semibold text-base text-[#1E293B] truncate pr-8 group-hover:text-[#2563EB] transition-colors">
                            {item.title}
                          </h3>
                          <span className="text-xs text-[#94A3B8] shrink-0 font-medium">{item.time}</span>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-1 mb-2 font-medium">
                          {item.preview}
                        </p>
                        
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#F1F5F9] text-[#475569] border border-transparent">
                            {item.category}
                          </span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            isCurrent ? 'bg-[#EFF6FF] text-[#2563EB]' : 'bg-slate-100 text-slate-400'
                          }`}>
                            {item.status}
                          </span>
                        </div>
                      </div>

                      {/* Quick hover actions */}
                      <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity self-center">
                        <button className="p-2 hover:bg-[#EFF6FF] rounded-lg text-slate-400 hover:text-[#2563EB]">
                          <Star className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={(e) => handleDelete(item.id, e)}
                          className="p-2 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  );
                })
              ) : (
                <div className="text-center py-12 text-[#94A3B8] text-sm">
                  没有找到匹配的对话记录
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
