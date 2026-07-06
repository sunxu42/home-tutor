import { useCallback, useEffect, useRef, useState } from 'react'
import { Loader2, Mic, MicOff, Volume2 } from 'lucide-react'

import { useVoiceShellHandlers } from '@/contexts/VoiceShellContext'
import { BARGE_IN_LEVEL, startPcmCapture, type PcmCaptureHandle } from '@/lib/pcm-capture'
import { PcmStreamPlayer } from '@/lib/pcm-player'
import { splitChineseSentences } from '@/lib/split-sentences'
import { SpeechSession, type SpeechSessionState } from '@/voice/SpeechSession'

type VoicePhase = 'idle' | 'listening' | 'thinking' | 'speaking'

function sessionStateToPhase(state: SpeechSessionState, chatLoading: boolean): VoicePhase {
  if (state === 'listening') {
    return 'listening'
  }
  if (state === 'speaking') {
    return 'speaking'
  }
  if (state === 'thinking' || chatLoading) {
    return 'thinking'
  }
  return 'idle'
}

export function VoiceShell() {
  const handlers = useVoiceShellHandlers()
  const [speechEnabled, setSpeechEnabled] = useState(false)
  const [phase, setPhase] = useState<VoicePhase>('idle')
  const [partialText, setPartialText] = useState('')
  const [error, setError] = useState<string | null>(null)

  const captureRef = useRef<PcmCaptureHandle | null>(null)
  const playerRef = useRef<PcmStreamPlayer | null>(null)
  const sessionRef = useRef<SpeechSession | null>(null)
  const spokenRef = useRef('')
  const queuedUtterancesRef = useRef<string[]>([])
  const speakingRef = useRef(false)
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  const stopCapture = useCallback(() => {
    captureRef.current?.stop()
    captureRef.current = null
  }, [])

  const stopPlayback = useCallback(() => {
    playerRef.current?.stop()
    playerRef.current = null
    sessionRef.current?.stopTts()
    speakingRef.current = false
    queuedUtterancesRef.current = []
  }, [])

  const beginListening = useCallback(async () => {
    const session = sessionRef.current
    if (!handlersRef.current || handlersRef.current.disabled || !speechEnabled || !session) {
      return
    }
    setError(null)
    setPartialText('')
    stopPlayback()
    session.startListening()
    try {
      const capture = await startPcmCapture((chunk, level) => {
        session.sendAudio(chunk)
        if (
          speakingRef.current &&
          level > BARGE_IN_LEVEL &&
          handlersRef.current?.onBargeIn
        ) {
          stopPlayback()
          handlersRef.current.onBargeIn()
          session.startListening()
        }
      })
      captureRef.current = capture
    } catch (err) {
      session.setReady()
      session.stopListening()
      setError(err instanceof Error ? err.message : '无法访问麦克风')
    }
  }, [speechEnabled, stopPlayback])

  const endListening = useCallback(() => {
    stopCapture()
    sessionRef.current?.stopListening()
  }, [stopCapture])

  const playNextUtterance = useCallback(() => {
    const session = sessionRef.current
    const next = queuedUtterancesRef.current.shift()
    if (!next || !session) {
      speakingRef.current = false
      session?.setReady()
      return
    }
    speakingRef.current = true
    if (!playerRef.current) {
      playerRef.current = new PcmStreamPlayer()
    }
    session.synthesize(next, crypto.randomUUID())
  }, [])

  useEffect(() => {
    const session = new SpeechSession()
    sessionRef.current = session

    void session.start({
      onSpeechReady: (enabled) => setSpeechEnabled(enabled),
      onStateChange: (state) => {
        if (state === 'disabled') {
          setSpeechEnabled(false)
        }
        setPhase(sessionStateToPhase(state, Boolean(handlersRef.current?.chatLoading)))
      },
      onAsrPartial: (text) => setPartialText(text),
      onAsrFinal: (text) => {
        setPartialText(text)
        void handlersRef.current?.onUserUtterance(text)
      },
      onTtsAudio: (chunk) => {
        playerRef.current?.enqueue(chunk)
      },
      onTtsEnded: () => {
        playNextUtterance()
      },
      onError: (message) => setError(message),
    })

    return () => {
      session.stop()
      sessionRef.current = null
      stopCapture()
      stopPlayback()
    }
  }, [playNextUtterance, stopCapture, stopPlayback])

  useEffect(() => {
    const assistantText = handlers?.assistantText ?? ''
    if (!assistantText || handlers?.chatLoading) {
      return
    }
    if (!assistantText.startsWith(spokenRef.current)) {
      spokenRef.current = ''
      queuedUtterancesRef.current = []
      stopPlayback()
    }
    const fresh = assistantText.slice(spokenRef.current.length).trim()
    if (!fresh) {
      return
    }
    const sentences = splitChineseSentences(fresh)
    if (sentences.length === 0) {
      return
    }
    spokenRef.current = assistantText
    queuedUtterancesRef.current.push(...sentences)
    if (!speakingRef.current && phase !== 'listening') {
      playNextUtterance()
    }
  }, [handlers?.assistantText, handlers?.chatLoading, phase, playNextUtterance, stopPlayback])

  useEffect(() => {
    const session = sessionRef.current
    if (!session) {
      return
    }
    if (handlers?.chatLoading) {
      session.setThinking()
      setPhase('thinking')
      return
    }
    if (phase === 'thinking') {
      setPhase(speakingRef.current ? 'speaking' : 'idle')
      if (!speakingRef.current) {
        session.setReady()
      }
    }
  }, [handlers?.chatLoading, phase])

  if (!speechEnabled || !handlers) {
    return null
  }

  const listening = phase === 'listening'
  const statusLabel =
    phase === 'listening'
      ? '正在聆听…'
      : phase === 'thinking'
        ? '老师思考中…'
        : phase === 'speaking'
          ? '老师讲解中…'
          : '语音助手'

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      <div className="pointer-events-auto w-full max-w-md rounded-2xl border border-border/70 bg-background/95 p-3 shadow-lg backdrop-blur">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              if (listening) {
                endListening()
              } else {
                void beginListening()
              }
            }}
            disabled={handlers.disabled || phase === 'thinking'}
            className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full border transition-colors ${
              listening
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border/70 bg-muted/40 text-foreground hover:bg-muted/70'
            }`}
            aria-label={listening ? '结束聆听' : '开始语音对话'}
          >
            {phase === 'thinking' ? (
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
            ) : listening ? (
              <MicOff className="h-5 w-5" aria-hidden />
            ) : (
              <Mic className="h-5 w-5" aria-hidden />
            )}
          </button>

          <div className="min-w-0 flex-1 rounded-lg bg-muted/25 px-3 py-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Volume2 className="h-3.5 w-3.5" aria-hidden />
              <span>{statusLabel}</span>
            </div>
            <p className="mt-1 line-clamp-2 text-sm text-foreground/90">
              {partialText || (phase === 'speaking' ? handlers.assistantText : '点击麦克风开始说话')}
            </p>
          </div>
        </div>
        {error ? <p className="mt-2 text-xs text-destructive">{error}</p> : null}
      </div>
    </div>
  )
}
