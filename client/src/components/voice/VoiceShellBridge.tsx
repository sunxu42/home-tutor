import { useVoiceShellRegistration, type VoiceShellHandlers } from '@/contexts/VoiceShellContext'

export function VoiceShellBridge({ handlers }: { handlers: VoiceShellHandlers | null }) {
  useVoiceShellRegistration(handlers)
  return null
}
