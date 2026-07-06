import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MutableRefObject } from 'react'
import {
  A2UIProvider,
  A2UIRenderer,
  injectStyles,
  useA2UIActions,
  useA2UIError,
  type A2UIClientEventMessage,
} from '@copilotkit/a2ui-renderer'
import { Loader2, Sparkles } from 'lucide-react'

import { homeTutorCatalog } from '@/components/a2ui/catalog'
import { TUTOR_SURFACE_ID } from '@/components/a2ui/definitions'
import { TutorExplanationPanel } from '@/components/session-review/TutorExplanationPanel'
import {
  ErrorCategoryBadge,
  FixtureBadge,
  VerdictBadge,
} from '@/components/session-review/SessionReviewBadges'
import { fingerprintA2UIMessages, fingerprintTutorSeed } from '@/lib/a2ui-fingerprint'
import { tutorContentToA2UI } from '@/lib/tutor-to-a2ui'
import type { A2UIMessage } from '@/types/a2ui'
import type { QuestionProcessPackage, TutorContent } from '@/types/session-review'

interface TutorA2UISurfaceProps {
  package: QuestionProcessPackage
  tutor: TutorContent
  messages: A2UIMessage[]
  onAction?: (actionId: string) => void
  onAnalyze?: () => void
  analyzing?: boolean
  chatLoading?: boolean
}

function handleA2UIAction(message: A2UIClientEventMessage, onAction?: (actionId: string) => void) {
  const actionId = message.userAction?.name
  if (actionId) {
    onAction?.(actionId)
  }
}

function resolveEffectiveMessages(args: {
  questionId: string
  messages: A2UIMessage[]
  seedMessages: A2UIMessage[]
  seedFingerprint: string
  chatLoading: boolean
  cache: MutableRefObject<{ questionId: string; messages: A2UIMessage[]; seedFingerprint: string }>
}): A2UIMessage[] {
  const { questionId, messages, seedMessages, seedFingerprint, chatLoading, cache } = args

  if (questionId !== cache.current.questionId) {
    const next = messages.length > 0 ? messages : seedMessages
    cache.current = { questionId, messages: next, seedFingerprint }
    return next
  }

  if (messages.length > 0) {
    const agentFingerprint = fingerprintA2UIMessages(messages)
    if (agentFingerprint !== seedFingerprint) {
      cache.current.messages = messages
      return messages
    }
  }

  if (chatLoading && cache.current.messages.length > 0) {
    return cache.current.messages
  }

  if (
    cache.current.seedFingerprint === seedFingerprint &&
    cache.current.messages.length > 0 &&
    fingerprintA2UIMessages(cache.current.messages) === seedFingerprint
  ) {
    return cache.current.messages
  }

  cache.current = { questionId, messages: seedMessages, seedFingerprint }
  return seedMessages
}

function useAppliedA2UIPayload(
  questionId: string,
  messagesFingerprint: string,
  payload: A2UIMessage[],
): boolean {
  const { processMessages } = useA2UIActions()
  const appliedKeyRef = useRef<string | null>(null)
  const [ready, setReady] = useState(() => payload.length > 0)

  useLayoutEffect(() => {
    const applyKey = `${questionId}:${messagesFingerprint}`

    if (payload.length === 0) {
      appliedKeyRef.current = null
      setReady(false)
      return
    }

    if (appliedKeyRef.current === applyKey) {
      setReady(true)
      return
    }

    processMessages(payload as Array<Record<string, unknown>>)
    appliedKeyRef.current = applyKey
    setReady(true)
  }, [messagesFingerprint, payload, processMessages, questionId])

  return ready
}

const A2UISurfaceViewport = memo(function A2UISurfaceViewport({
  analysisLoading,
  surfaceReady,
}: {
  analysisLoading: boolean
  surfaceReady: boolean
}) {
  if (!surfaceReady && !analysisLoading) {
    return (
      <div className="a2ui-surface-placeholder min-h-[4rem] rounded-lg bg-muted/20" aria-busy="true" />
    )
  }

  return (
    <div className="a2ui-surface-host space-y-2 rounded-lg bg-muted/20 p-3">
      <A2UIRenderer surfaceId={TUTOR_SURFACE_ID} loadingFallback={null} />
    </div>
  )
})

function TutorA2UISurfaceContent({
  package: pkg,
  tutor,
  messages,
  onAnalyze,
  analyzing = false,
  chatLoading = false,
}: TutorA2UISurfaceProps) {
  const a2uiError = useA2UIError()

  const questionId = tutor.question_id
  const studentAnswer = pkg.final_answer.text

  const tutorSeedFingerprint = useMemo(
    () => fingerprintTutorSeed(tutor, studentAnswer),
    [studentAnswer, tutor],
  )

  const seedMessages = useMemo(
    () => tutorContentToA2UI(tutor, { studentAnswer }),
    [studentAnswer, tutorSeedFingerprint, tutor],
  )

  const stableMessagesRef = useRef({
    questionId,
    messages: seedMessages,
    seedFingerprint: tutorSeedFingerprint,
  })

  const effectiveMessages = useMemo(
    () =>
      resolveEffectiveMessages({
        questionId,
        messages,
        seedMessages,
        seedFingerprint: tutorSeedFingerprint,
        chatLoading,
        cache: stableMessagesRef,
      }),
    [chatLoading, messages, questionId, seedMessages, tutorSeedFingerprint],
  )

  const messagesFingerprint = useMemo(
    () => fingerprintA2UIMessages(effectiveMessages),
    [effectiveMessages],
  )

  const surfaceReady = useAppliedA2UIPayload(questionId, messagesFingerprint, effectiveMessages)

  useEffect(() => {
    injectStyles()
  }, [])

  const isFixtureTutor = tutor.analysis_status === 'ready' && Boolean(tutor.model?.startsWith('mock'))
  const analysisLoading =
    analyzing || tutor.analysis_status === 'generating' || tutor.analysis_status === 'pending'
  const hasRenderableSurface = effectiveMessages.length > 0

  if (a2uiError || (!hasRenderableSurface && tutor.analysis_status !== 'ready')) {
    return (
      <TutorExplanationPanel
        package={pkg}
        tutor={tutor}
        onAnalyze={onAnalyze}
        analyzing={analyzing}
      />
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b border-border/50 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden />
            <h2 className="text-base font-semibold">AI 讲解</h2>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {isFixtureTutor ? <FixtureBadge /> : null}
            {tutor.error_classification ? (
              <ErrorCategoryBadge category={tutor.error_classification.category} />
            ) : null}
            <VerdictBadge verdict={tutor.verdict} />
          </div>
        </div>
        {tutor.summary ? (
          <p className="mt-2 text-sm font-medium leading-snug">{tutor.summary}</p>
        ) : null}
        {onAnalyze ? (
          <button
            type="button"
            onClick={onAnalyze}
            disabled={analyzing}
            className="mt-2 inline-flex cursor-pointer items-center gap-2 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {analyzing ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
            AI 分析
          </button>
        ) : null}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pt-3">
        {analysisLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden />
            AI 正在分析…
          </div>
        ) : null}

        <A2UISurfaceViewport analysisLoading={analysisLoading} surfaceReady={surfaceReady} />

        {chatLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden />
            老师正在回复…
          </div>
        ) : null}
      </div>
    </div>
  )
}

export const TutorA2UISurface = memo(function TutorA2UISurface(props: TutorA2UISurfaceProps) {
  const onAction = useCallback(
    (message: A2UIClientEventMessage) => handleA2UIAction(message, props.onAction),
    [props.onAction],
  )

  return (
    <A2UIProvider
      key={props.package.question_id}
      catalog={homeTutorCatalog}
      onAction={onAction}
    >
      <TutorA2UISurfaceContent {...props} />
    </A2UIProvider>
  )
}, (prev, next) => {
  return (
    prev.package.question_id === next.package.question_id &&
    prev.package.final_answer.text === next.package.final_answer.text &&
    fingerprintTutorSeed(prev.tutor, prev.package.final_answer.text) ===
      fingerprintTutorSeed(next.tutor, next.package.final_answer.text) &&
    fingerprintA2UIMessages(prev.messages) === fingerprintA2UIMessages(next.messages) &&
    prev.analyzing === next.analyzing &&
    prev.chatLoading === next.chatLoading &&
    prev.onAnalyze === next.onAnalyze &&
    prev.onAction === next.onAction
  )
})
