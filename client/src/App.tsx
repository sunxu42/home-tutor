import { useCallback, useEffect, useState } from 'react'

import { api, type Session, type Subject } from '@/services/api'
import { HomePage } from '@/pages/HomePage'

function App() {
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
      // subjects are static, fallback to hardcoded list
      setSubjects(['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理'])
    }
  }, [])

  useEffect(() => {
    fetchSubjects()
  }, [fetchSubjects])

  useEffect(() => {
    fetchSessions(selectedSubject ?? undefined)
  }, [fetchSessions, selectedSubject])

  return (
    <HomePage
      sessions={sessions}
      subjects={subjects}
      selectedSubject={selectedSubject}
      onSelectSubject={setSelectedSubject}
      loading={loading}
      error={error}
    />
  )
}

export default App
