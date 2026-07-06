import { useSessions } from '@/hooks/useSessions'
import { HomePage } from '@/pages/HomePage'

function App() {
  const {
    sessions,
    subjects,
    selectedSubject,
    setSelectedSubject,
    loading,
    error,
  } = useSessions()

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
