import { useCallback, useState, type ReactNode } from 'react'

import { VoiceShell } from '@/components/voice/VoiceShell'
import { VoiceShellProvider, type VoiceShellHandlers } from '@/contexts/VoiceShellContext'

export function VoiceShellRoot({ children }: { children: ReactNode }) {
  const [handlers, setHandlers] = useState<VoiceShellHandlers | null>(null)

  const registerHandlers = useCallback((next: VoiceShellHandlers | null) => {
    setHandlers(next)
  }, [])

  return (
    <VoiceShellProvider handlers={handlers} onHandlersChange={registerHandlers}>
      {children}
      <VoiceShell />
    </VoiceShellProvider>
  )
}
