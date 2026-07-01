import type { QuestionDetailResponse, TutorContent, TutorViewResponse } from '@/types/session-review'
import { request } from '@/services/api'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export const sessionReviewApi = {
  getTutorView: (sessionId: string) =>
    request<TutorViewResponse>(`/sessions/${sessionId}/tutor-view`),

  getQuestion: (sessionId: string, questionId: string) =>
    request<QuestionDetailResponse>(`/sessions/${sessionId}/questions/${questionId}`),

  analyze: (sessionId: string, questionId: string) =>
    request<{ analysis_status: string }>(
      `/sessions/${sessionId}/questions/${questionId}/analyze`,
      { method: 'POST' },
    ),

  subscribeTutorEvents: (
    sessionId: string,
    questionId: string,
    handlers: {
      onStatus?: (status: string) => void
      onTutor?: (tutor: TutorContent) => void
      onError?: (message: string) => void
    },
  ): EventSource => {
    const url = `${API_BASE}/sessions/${sessionId}/questions/${questionId}/tutor/events`
    const source = new EventSource(url)

    source.addEventListener('status', (event) => {
      const data = JSON.parse((event as MessageEvent).data) as { analysis_status: string }
      handlers.onStatus?.(data.analysis_status)
    })

    source.addEventListener('tutor', (event) => {
      const tutor = JSON.parse((event as MessageEvent).data) as TutorContent
      handlers.onTutor?.(tutor)
      source.close()
    })

    source.addEventListener('error', (event) => {
      if (event instanceof MessageEvent) {
        const data = JSON.parse(event.data) as { error?: string }
        handlers.onError?.(data.error ?? '分析失败')
        source.close()
      }
    })

    return source
  },
}
