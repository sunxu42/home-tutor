import { useCallback, useEffect, useState } from 'react'

import { api, type Session, type Subject } from '@/services/api'

const FALLBACK_SUBJECTS: Subject[] = [
  '语文',
  '数学',
  '英语',
  '物理',
  '化学',
  '生物',
  '政治',
  '历史',
  '地理',
]

export interface UseSessionsResult {
  sessions: Session[]
  subjects: Subject[]
  selectedSubject: Subject | null
  setSelectedSubject: (subject: Subject | null) => void
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useSessions(): UseSessionsResult {
  const [sessions, setSessions] = useState<Session[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSessions = useCallback(async (subject?: Subject) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.sessions.list(subject)
      setSessions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '无法连接后端')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchSubjects = useCallback(async () => {
    try {
      const data = await api.subjects()
      setSubjects(data)
    } catch {
      setSubjects(FALLBACK_SUBJECTS)
    }
  }, [])

  useEffect(() => {
    void fetchSubjects()
  }, [fetchSubjects])

  useEffect(() => {
    void fetchSessions(selectedSubject ?? undefined)
  }, [fetchSessions, selectedSubject])

  const refetch = useCallback(() => {
    void fetchSessions(selectedSubject ?? undefined)
  }, [fetchSessions, selectedSubject])

  return {
    sessions,
    subjects,
    selectedSubject,
    setSelectedSubject,
    loading,
    error,
    refetch,
  }
}
