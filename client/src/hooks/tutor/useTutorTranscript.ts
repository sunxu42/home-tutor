import { useCallback, useEffect, useState } from 'react'

import type { TranscriptEntry } from '@/types/tutor-session-context'

export function useTutorTranscript(questionId: string) {
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [recentActions, setRecentActions] = useState<Array<{ id: string; ts: number }>>([])

  useEffect(() => {
    setTranscript([])
    setRecentActions([])
  }, [questionId])

  const appendTranscript = useCallback((entry: TranscriptEntry) => {
    setTranscript((prev) => [...prev, entry])
  }, [])

  const recordAction = useCallback((actionId: string) => {
    setRecentActions((prev) => [...prev, { id: actionId, ts: Date.now() }])
  }, [])

  const syncAssistantMessage = useCallback((assistantPreview: string, isLoading: boolean) => {
    if (isLoading || !assistantPreview) {
      return
    }
    setTranscript((prev) => {
      const last = prev[prev.length - 1]
      if (last?.role === 'assistant' && last.content === assistantPreview) {
        return prev
      }
      return [
        ...prev,
        { role: 'assistant', content: assistantPreview, source: 'text', ts: Date.now() },
      ]
    })
  }, [])

  return {
    transcript,
    recentActions,
    appendTranscript,
    recordAction,
    syncAssistantMessage,
  }
}
