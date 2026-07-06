type SpeechServerMessage =
  | { type: 'ready'; enabled: boolean }
  | { type: 'asr_started' }
  | { type: 'asr_partial'; text: string }
  | { type: 'asr_final'; text: string }
  | { type: 'asr_stopped' }
  | { type: 'tts_started'; utteranceId: string }
  | { type: 'tts_ended'; utteranceId: string }
  | { type: 'error'; code: string; message: string }
  | { type: 'pong' }

export type SpeechGatewayStatus = 'disconnected' | 'connecting' | 'ready' | 'disabled'

export interface SpeechGatewayCallbacks {
  onReady?: (payload: { enabled: boolean }) => void
  onAsrPartial?: (text: string) => void
  onAsrFinal?: (text: string) => void
  onTtsStarted?: (utteranceId: string) => void
  onTtsAudio?: (chunk: ArrayBuffer, utteranceId?: string) => void
  onTtsEnded?: (utteranceId: string) => void
  onError?: (message: string) => void
  onStatusChange?: (status: SpeechGatewayStatus) => void
}

export class SpeechGatewayClient {
  private socket: WebSocket | null = null
  private callbacks: SpeechGatewayCallbacks = {}
  private status: SpeechGatewayStatus = 'disconnected'
  private activeUtteranceId: string | null = null
  private reconnectTimer: number | null = null
  private terminalDisabled = false
  private connectUrl: string | null = null

  connect(url: string, callbacks: SpeechGatewayCallbacks = {}): void {
    if (this.terminalDisabled) {
      this.setStatus('disabled')
      return
    }

    this.callbacks = callbacks
    this.connectUrl = url

    if (this.socket?.readyState === WebSocket.OPEN) {
      return
    }

    this.setStatus('connecting')
    const socket = new WebSocket(url)
    socket.binaryType = 'arraybuffer'
    this.socket = socket

    socket.onopen = () => {
      if (this.reconnectTimer !== null) {
        window.clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
    }

    socket.onmessage = (event) => {
      if (typeof event.data === 'string') {
        this.handleTextMessage(event.data)
        return
      }
      if (event.data instanceof ArrayBuffer) {
        this.callbacks.onTtsAudio?.(event.data, this.activeUtteranceId ?? undefined)
      }
    }

    socket.onerror = () => {
      this.callbacks.onError?.('语音服务连接失败')
    }

    socket.onclose = () => {
      this.socket = null
      if (this.terminalDisabled || this.status === 'disabled') {
        this.setStatus('disabled')
        return
      }
      this.setStatus('disconnected')
      if (this.connectUrl) {
        this.reconnectTimer = window.setTimeout(() => {
          if (this.connectUrl) {
            this.connect(this.connectUrl, this.callbacks)
          }
        }, 3000)
      }
    }
  }

  disconnect(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.connectUrl = null
    this.socket?.close()
    this.socket = null
    if (!this.terminalDisabled) {
      this.setStatus('disconnected')
    }
  }

  getStatus(): SpeechGatewayStatus {
    return this.status
  }

  isTerminalDisabled(): boolean {
    return this.terminalDisabled
  }

  startAsr(): void {
    this.sendJson({ type: 'asr_start' })
  }

  stopAsr(): void {
    this.sendJson({ type: 'asr_stop' })
  }

  sendAudio(chunk: ArrayBuffer): void {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return
    }
    this.socket.send(chunk)
  }

  synthesize(text: string, utteranceId: string): void {
    this.activeUtteranceId = utteranceId
    this.sendJson({ type: 'tts_start', text, utteranceId })
  }

  stopTts(): void {
    this.sendJson({ type: 'tts_stop' })
    this.activeUtteranceId = null
  }

  private handleTextMessage(raw: string): void {
    let payload: SpeechServerMessage
    try {
      payload = JSON.parse(raw) as SpeechServerMessage
    } catch {
      this.callbacks.onError?.('语音服务返回无效 JSON')
      return
    }

    switch (payload.type) {
      case 'ready':
        if (!payload.enabled) {
          this.terminalDisabled = true
          this.setStatus('disabled')
        } else {
          this.setStatus('ready')
        }
        this.callbacks.onReady?.({ enabled: payload.enabled })
        break
      case 'asr_started':
        break
      case 'asr_partial':
        this.callbacks.onAsrPartial?.(payload.text)
        break
      case 'asr_final':
        this.callbacks.onAsrFinal?.(payload.text)
        break
      case 'asr_stopped':
        break
      case 'tts_started':
        this.activeUtteranceId = payload.utteranceId
        this.callbacks.onTtsStarted?.(payload.utteranceId)
        break
      case 'tts_ended':
        this.callbacks.onTtsEnded?.(payload.utteranceId)
        if (this.activeUtteranceId === payload.utteranceId) {
          this.activeUtteranceId = null
        }
        break
      case 'error':
        this.callbacks.onError?.(payload.message)
        break
      default:
        break
    }
  }

  private sendJson(payload: Record<string, unknown>): void {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return
    }
    this.socket.send(JSON.stringify(payload))
  }

  private setStatus(status: SpeechGatewayStatus): void {
    this.status = status
    this.callbacks.onStatusChange?.(status)
  }
}

export const speechGateway = new SpeechGatewayClient()
