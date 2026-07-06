import { SpeechGatewayClient, type SpeechGatewayCallbacks } from '@/services/speechGateway'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export type SpeechSessionState =
  | 'idle'
  | 'connecting'
  | 'ready'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'error'
  | 'disabled'

export interface SpeechSessionCallbacks {
  onStateChange?: (state: SpeechSessionState) => void
  onSpeechReady?: (enabled: boolean) => void
  onAsrPartial?: (text: string) => void
  onAsrFinal?: (text: string) => void
  onTtsAudio?: (chunk: ArrayBuffer) => void
  onTtsEnded?: () => void
  onError?: (message: string) => void
}

function resolveSpeechWsBaseUrl(): string {
  const configured = import.meta.env.VITE_SPEECH_WS_URL
  if (configured) {
    return configured
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/speech`
}

function buildSpeechWsUrl(token: string): string {
  const url = new URL(resolveSpeechWsBaseUrl(), window.location.origin)
  url.searchParams.set('token', token)
  return url.toString()
}

async function fetchWsToken(): Promise<{ token?: string; enabled?: boolean }> {
  const response = await fetch(`${API_BASE}/speech/ws-token`)
  if (!response.ok) {
    if (response.status === 503) {
      return { enabled: false }
    }
    const detail = await response.text()
    throw new Error(detail || '无法获取语音令牌')
  }
  const payload = (await response.json()) as { token?: string; enabled?: boolean }
  if (payload.enabled === false) {
    return { enabled: false }
  }
  if (!payload.token) {
    throw new Error('语音令牌无效')
  }
  return payload
}

export class SpeechSession {
  private readonly gateway = new SpeechGatewayClient()
  private state: SpeechSessionState = 'idle'
  private callbacks: SpeechSessionCallbacks = {}
  private speechEnabled = false

  getState(): SpeechSessionState {
    return this.state
  }

  isSpeechEnabled(): boolean {
    return this.speechEnabled
  }

  async start(callbacks: SpeechSessionCallbacks): Promise<void> {
    this.callbacks = callbacks
    if (this.state === 'disabled') {
      return
    }

    this.transition('connecting')

    try {
      const tokenPayload = await fetchWsToken()
      if (tokenPayload.enabled === false || !tokenPayload.token) {
        this.speechEnabled = false
        this.callbacks.onSpeechReady?.(false)
        this.transition('disabled')
        return
      }

      const url = buildSpeechWsUrl(tokenPayload.token)
      const gatewayCallbacks: SpeechGatewayCallbacks = {
        onReady: ({ enabled }) => {
          this.speechEnabled = enabled
          this.callbacks.onSpeechReady?.(enabled)
          if (!enabled) {
            this.transition('disabled')
            return
          }
          if (this.state === 'connecting' || this.state === 'error') {
            this.transition('ready')
          }
        },
        onAsrPartial: (text) => this.callbacks.onAsrPartial?.(text),
        onAsrFinal: (text) => {
          this.callbacks.onAsrFinal?.(text)
          this.transition('thinking')
        },
        onTtsStarted: () => this.transition('speaking'),
        onTtsAudio: (chunk) => this.callbacks.onTtsAudio?.(chunk),
        onTtsEnded: () => {
          this.callbacks.onTtsEnded?.()
          if (this.state === 'speaking') {
            this.transition('ready')
          }
        },
        onError: (message) => {
          this.callbacks.onError?.(message)
          if (this.state !== 'disabled') {
            this.transition('error')
          }
        },
        onStatusChange: (status) => {
          if (status === 'disabled') {
            this.speechEnabled = false
            this.transition('disabled')
          }
        },
      }

      this.gateway.connect(url, gatewayCallbacks)
    } catch (err) {
      const message = err instanceof Error ? err.message : '语音服务初始化失败'
      this.callbacks.onError?.(message)
      this.transition('error')
    }
  }

  stop(): void {
    this.gateway.disconnect()
    if (this.state !== 'disabled') {
      this.transition('idle')
    }
    this.speechEnabled = false
  }

  startListening(): void {
    if (!this.speechEnabled || this.state === 'disabled') {
      return
    }
    this.gateway.startAsr()
    this.transition('listening')
  }

  stopListening(): void {
    if (this.state !== 'listening') {
      return
    }
    this.gateway.stopAsr()
    this.transition('thinking')
  }

  sendAudio(chunk: ArrayBuffer): void {
    this.gateway.sendAudio(chunk)
  }

  synthesize(text: string, utteranceId: string): void {
    if (!this.speechEnabled || this.state === 'disabled') {
      return
    }
    this.gateway.synthesize(text, utteranceId)
    this.transition('speaking')
  }

  stopTts(): void {
    this.gateway.stopTts()
    if (this.state === 'speaking') {
      this.transition(this.speechEnabled ? 'ready' : 'idle')
    }
  }

  setThinking(): void {
    if (this.state !== 'disabled') {
      this.transition('thinking')
    }
  }

  setReady(): void {
    if (this.speechEnabled && this.state !== 'disabled') {
      this.transition('ready')
    }
  }

  private transition(next: SpeechSessionState): void {
    if (this.state === next) {
      return
    }
    this.state = next
    this.callbacks.onStateChange?.(next)
  }
}
