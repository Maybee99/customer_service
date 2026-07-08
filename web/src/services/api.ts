const API_BASE = 'http://localhost:8000/api';

export interface StepEvent {
  type: 'thinking' | 'tool' | 'result' | 'reflect';
  content: string;
}

export async function sendChatMessageStream(
  question: string,
  sessionId: string,
  userId: string,
  userName: string,
  onStep: (step: StepEvent) => void,
  onAnswerToken: (token: string) => void,
  onDone: (data: { session_id: string; needs_human: boolean }) => void,
  onError: (err: string) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId, user_id: userId, user_name: userName }),
  });

  if (!response.ok) { onError(await response.text()); return; }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith('event: ')) {
        currentEvent = trimmed.slice(7).trim();
        continue;
      }

      if (trimmed.startsWith('data: ')) {
        try {
          const data = JSON.parse(trimmed.slice(6).trim());

          switch (currentEvent) {
            case 'step':
              onStep(data as StepEvent);
              break;
            case 'answer_token':
              if (data.content) {
                onAnswerToken(data.content);
              }
              break;
            case 'done':
              onDone(data);
              break;
            case 'error':
              onError(data.detail || 'Unknown error');
              break;
          }
        } catch { /* skip malformed JSON */ }
        currentEvent = '';
      }
    }
  }
}

export async function fetchConversations(userId: string) {
  const res = await fetch(`${API_BASE}/conversations?user_id=${userId}`);
  return res.json();
}

export async function fetchConversationDetail(id: number) {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  return res.json();
}

export async function closeConversation(id: number) {
  const res = await fetch(`${API_BASE}/conversations/${id}/close`, { method: 'POST' });
  return res.json();
}

export async function deleteConversation(id: number): Promise<{ status: string; id: number }> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
}

// ── Knowledge Base ──────────────────────────────────────

export async function uploadKnowledgeFile(file: File, category: string): Promise<{
  id: number; status: string; original_filename: string;
}> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  formData.append('parse_mode', 'chunk');
  const res = await fetch(`${API_BASE}/knowledge/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail?.message || err.detail || 'Upload failed');
  }
  return res.json();
}

export async function fetchKnowledgeFiles(params?: {
  page?: number; page_size?: number; category?: string; status?: string;
}): Promise<{
  files: Array<{
    id: number; original_filename: string; file_type: string;
    file_size: number; category: string; parse_mode: string;
    chunk_count: number; status: string; error_message?: string;
    created_at: string; updated_at: string;
  }>;
  total: number; page: number; page_size: number; total_pages: number;
}> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.category) searchParams.set('category', params.category);
  if (params?.status) searchParams.set('status', params.status);
  const qs = searchParams.toString();
  const res = await fetch(`${API_BASE}/knowledge/files${qs ? '?' + qs : ''}`);
  return res.json();
}

export async function deleteKnowledgeFile(id: number): Promise<{
  status: string; deleted_chunks: number; original_filename: string;
}> {
  const res = await fetch(`${API_BASE}/knowledge/files/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
}

export async function reindexKnowledgeFile(id: number): Promise<{ id: number; status: string }> {
  const res = await fetch(`${API_BASE}/knowledge/files/${id}/reindex`, { method: 'POST' });
  if (!res.ok) throw new Error('Reindex failed');
  return res.json();
}
