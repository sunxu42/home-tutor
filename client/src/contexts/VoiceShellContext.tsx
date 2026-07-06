import { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react'

export interface VoiceShellHandlers {
  disabled: boolean
  onUserUtterance: (text: string) => void | Promise<void>
  onBargeIn?: () => void
  assistantText: string
  chatLoading: boolean
}

interface VoiceShellContextValue {
  handlers: VoiceShellHandlers | null
  registerHandlers: (handlers: VoiceShellHandlers | null) => void
}

const VoiceShellContext = createContext<VoiceShellContextValue | null>(null)

export function VoiceShellProvider({
  children,
  handlers,
  onHandlersChange,
}: {
  children: ReactNode
  handlers: VoiceShellHandlers | null
  onHandlersChange: (handlers: VoiceShellHandlers | null) => void
}) {
  const value = useMemo(
    () => ({
      handlers,
      registerHandlers: onHandlersChange,
    }),
    [handlers, onHandlersChange],
  )
  return <VoiceShellContext.Provider value={value}>{children}</VoiceShellContext.Provider>
}

export function useVoiceShellRegistration(handlers: VoiceShellHandlers | null): void {
  const context = useContext(VoiceShellContext)
  useEffect(() => {
    if (!context) {
      return
    }
    context.registerHandlers(handlers)
    return () => context.registerHandlers(null)
  }, [context, handlers])
}

export function useVoiceShellHandlers(): VoiceShellHandlers | null {
  return useContext(VoiceShellContext)?.handlers ?? null
}
