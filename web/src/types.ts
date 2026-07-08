/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export enum ScreenType {
  MAIN_CHAT = 'MAIN_CHAT',
  HISTORY = 'HISTORY',
  KNOWLEDGE = 'KNOWLEDGE',
  SETTINGS = 'SETTINGS',
}

export interface Message {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: string;
  sourcePdf?: string;
}

export interface SidebarChat {
  id: string;
  title: string;
  time: string;
  preview: string;
  active?: boolean;
}

export interface HistoryItem {
  id: string;
  title: string;
  time: string;
  preview: string;
  category: string;
  status: string; // e.g. '当前对话', '对话中', '已解决'
}

export interface KBDocument {
  id: string;
  name: string;
  category: string;
  size: string;
  updatedAt: string;
  status: '已索引' | '解析中' | '同步中';
}

export interface UserProfile {
  name: string;
  role: string;
  email: string;
  employeeId?: string;
  avatarUrl?: string;
}
