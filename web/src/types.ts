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

export interface StepEvent {
  type: 'thinking' | 'tool' | 'result' | 'reflect';
  content: string;
}

export interface Conversation {
  id: number;
  session_id: string;
  user_id: string;
  title: string;
  preview: string;
  message_count: number;
  status: string;
  created_at: string;
  updated_at: string;
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
  status: string;
}

export interface KnowledgeFileItem {
  id: number;
  original_filename: string;
  file_type: string;
  file_size: number;
  category: string;
  parse_mode: string;
  chunk_count: number;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface KBDocument {
  id: string;
  name: string;
  category: string;
  size: string;
  updatedAt: string;
  status: string;
}

export interface UserProfile {
  name: string;
  role: string;
  email: string;
  employeeId?: string;
  avatarUrl?: string;
}
