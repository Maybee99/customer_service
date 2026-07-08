/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { SidebarChat, HistoryItem, KBDocument, UserProfile, Message } from './types';

// =================== MAIN CHAT DATA ===================
export const mainChatSidebar: SidebarChat[] = [
  {
    id: 'mc_1',
    title: '公司入职五险一金政策',
    time: '10:30 AM',
    preview: '你好，我想了解一下公司的入职...',
    active: true,
  },
  {
    id: 'mc_2',
    title: '如何申请办公用品',
    time: '昨天',
    preview: '我的工位需要一个新的显示器支架',
  },
  {
    id: 'mc_3',
    title: '报销流程咨询',
    time: '周一',
    preview: '请问出差的打车票如何报销？',
  },
  {
    id: 'mc_4',
    title: '内推奖励政策',
    time: '2月15日',
    preview: '如果推荐的高级工程师入职...',
  },
];

export const initialChatMessages: Message[] = [
  {
    id: 'msg_1',
    sender: 'user',
    content: '你好，我想了解一下公司的入职五险一金政策。',
    timestamp: '10:30 AM',
  },
  {
    id: 'msg_2',
    sender: 'ai',
    content: `您好！关于公司的五险一金政策，主要包含以下几点：

1. **养老保险**：按工资基数的 8% 缴纳。
2. **公积金**：按工资基数的 12% 缴纳，公司 1:1 配比。
3. **医疗保险**：覆盖门诊与住院报销。`,
    timestamp: '10:31 AM',
    sourcePdf: '2024年度员工手册-福利篇.pdf',
  },
];

export const mainChatUser: UserProfile = {
  name: 'User Profile',
  role: 'Employee ID: 8829',
  email: '',
};

// =================== HISTORY DATA ===================
export const historySidebar: SidebarChat[] = [
  {
    id: 'hist_1',
    title: '入职五险一金政策咨询',
    time: '14:32',
    preview: '入职五险一金政策咨询',
    active: true,
  },
  {
    id: 'hist_2',
    title: '出差交通费报销标准查询',
    time: '10:15',
    preview: '出差交通费报销标准查询',
  },
  {
    id: 'hist_3',
    title: 'VPN 远程办公连接失败排查',
    time: '昨天',
    preview: 'VPN 远程办公连接失败排查',
  },
  {
    id: 'hist_4',
    title: '周报模版及撰写规范咨询',
    time: '昨天',
    preview: '周报模版及撰写规范咨询',
  },
  {
    id: 'hist_5',
    title: '年终奖税务计算方法说明',
    time: '更早',
    preview: '年终奖税务计算方法说明',
  },
];

export const historyItems: HistoryItem[] = [
  {
    id: 'hist_item_1',
    title: '入职五险一金政策咨询',
    time: '14:32',
    preview: '关于新员工入职后的五险一金缴纳基数，以及公积金提取的详细流程说明...',
    category: '人力资源',
    status: '当前对话',
  },
  {
    id: 'hist_item_2',
    title: '出差交通费报销标准查询',
    time: '10:15',
    preview: '北京到上海的高铁二等座报销标准，以及打车费的额度限制规定...',
    category: '财务报销',
    status: '对话中',
  },
  {
    id: 'hist_item_3',
    title: 'VPN 远程办公连接失败排查',
    time: '17:45',
    preview: '尝试使用公司 VPN 账号登录时提示“证书已过期”，需协助更新证书或找回账号密码...',
    category: '技术支持',
    status: '已解决',
  },
];

export const historyUser: UserProfile = {
  name: 'User Profile',
  role: 'Premium Account',
  email: '',
  avatarUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCBegI1LaY8L_prySOntGR6MNbqCOo6ZYZdMzoCEC-degZnpbn51B3KM6MmI-QKpjmHbUiD2IXlsTPN45MIJVgaFPNs9sF0fJ0Rea3rroE1RggUaHe1roX4kl9iMtVGoJIDM90h6IfN3dUsE2owMMVfIyeOFv_Im0diFKTeKSYgQLANo8Yc0ss2iQ3hWGwEdCCrrRdZ1rIBMhUxPmbqH_yDdMKJr7N2esbpUMgPAjRugE9VcK9yy6zXvmdUxFdbe1E-rRHOFEsiPY4',
};

// =================== KNOWLEDGE DATA ===================
export const knowledgeSidebar: SidebarChat[] = [
  {
    id: 'kb_1',
    title: '关于2024福利政策咨询',
    time: '14:20',
    preview: '请问明年的带薪年假天数是否有调整？',
  },
  {
    id: 'kb_2',
    title: '智能客服插件集成指南',
    time: '昨天',
    preview: '在React项目中如何快速部署聊天窗口...',
  },
  {
    id: 'kb_3',
    title: '知识库文档同步失败',
    time: '周三',
    preview: '上传了5个PDF文件，其中3个显示索引失败...',
  },
  {
    id: 'kb_4',
    title: '费用报销流程确认',
    time: '周二',
    preview: '差旅补助的上限是每天多少元？',
  },
];

export const kbDocuments: KBDocument[] = [
  {
    id: 'kb_doc_1',
    name: '2024员工入职手册.pdf',
    category: '公司规章',
    size: '2.4 MB',
    updatedAt: '2024-03-24 14:20',
    status: '已索引',
  },
  {
    id: 'kb_doc_2',
    name: '智能客服话术库_V2.docx',
    category: '客服话术',
    size: '1.1 MB',
    updatedAt: '2024-03-22 09:15',
    status: '已索引',
  },
  {
    id: 'kb_doc_3',
    name: '产品常见问题清单.xlsx',
    category: '常见问题',
    size: '856 KB',
    updatedAt: '2024-03-21 16:40',
    status: '解析中',
  },
];

export const knowledgeUser: UserProfile = {
  name: 'Admin User',
  role: 'admin@corp.ai',
  email: 'admin@corp.ai',
  avatarUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDYFWP1Rb-4sXLbMooU4bqEm_INSLHIxvffhydIuvcTEONrjnmD3GnOOgQmbBInsZHHOUeVvq0T-H9CazMbSJ7fWDkMmT3N2Q_MR0NHQanOmp99HnYNn82BrTyRksvkGTKyjVRuG-8819-dv-NaHNawafeC2jY1prc9Xmpw-2QTU7BIVdymsI3sGG3jUeo8VCD6mEwZ7dJrxXWWE6TFJP9rLNKpfUntKFQrjs9dmBuBR2kjFsnKIkDaWHlkF56gSbJfB7DpE8MubPg',
};

// =================== SETTINGS DATA ===================
export const settingsSidebar: SidebarChat[] = [
  {
    id: 'set_1',
    title: '关于 2024 年度财务报表审计...',
    time: '2小时前',
    preview: '关于 2024 年度财务报表审计...',
    active: true,
  },
  {
    id: 'set_2',
    title: '季度销售策略分析',
    time: '5小时前',
    preview: '季度销售策略分析',
  },
  {
    id: 'set_3',
    title: '新员工入职流程咨询',
    time: '昨天 14:20',
    preview: '新员工入职流程咨询',
  },
  {
    id: 'set_4',
    title: '知识库搜索：差旅报销流程',
    time: '昨天 09:15',
    preview: '知识库搜索：差旅报销流程',
  },
  {
    id: 'set_5',
    title: 'IT 系统访问权限申请协助',
    time: '昨天 08:30',
    preview: 'IT 系统访问权限申请协助',
  },
];

export const settingsUser: UserProfile = {
  name: '张经理',
  role: 'Premium Account',
  email: 'zhang.manager@corporate.com',
  avatarUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCB2UpILt2CWAgbpSkQLnkt0OvIDI9WCLE1p8wgiVgDAKq6ZpDtNEvfKuPxkgtzkaSEiDz0NndOczKdcqqR5E3OGPv5CwJhHdJGItVVdghOmGNToiW6YAUoT3LVOdnTgnQ7OH1hhLMSHMydh3utIMqxoLMGE1EKtaVzRnv9euiKGIK8G7uG8ItHvgYvUey7tAp5OX8IBJWyTfXtSpwBjv1m9A0GS1MZf5LXmXQXIzUoccvj4Hb8AGEb8pFWBBCIEoH7yCYr1-GpEIE',
};
