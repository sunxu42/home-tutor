const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export { API_BASE }

export type Subject =
  | '语文'
  | '数学'
  | '英语'
  | '物理'
  | '化学'
  | '生物'
  | '政治'
  | '历史'
  | '地理'

export interface Session {
  id: string
  subject: Subject
  session_time: string
  accuracy: number
  created_at: string
  updated_at: string
}

export interface SessionCreate {
  id?: string
  subject: Subject
  session_time: string
  accuracy: number
}

export interface SessionUpdate {
  subject?: Subject
  session_time?: string
  accuracy?: number
}

async function parseErrorMessage(response: Response): Promise<string> {
  const fallback = `HTTP ${response.status}: ${response.statusText}`
  try {
    const body = (await response.json()) as { detail?: string }
    if (typeof body.detail === 'string' && body.detail.length > 0) {
      return body.detail
    }
  } catch {
    // ignore non-JSON error bodies
  }
  return fallback
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  sessions: {
    list: (subject?: Subject) =>
      request<Session[]>(
        subject ? `/sessions?subject=${encodeURIComponent(subject)}` : '/sessions'
      ),
    get: (id: string) => request<Session>(`/sessions/${id}`),
    create: (data: SessionCreate) =>
      request<Session>('/sessions', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: SessionUpdate) =>
      request<Session>(`/sessions/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<{ ok: boolean }>(`/sessions/${id}`, { method: 'DELETE' }),
  },

  subjects: () => request<Subject[]>('/subjects'),
}
