import { useAgentContext, type JsonSerializable } from '@copilotkit/react-core/v2'
import { useCallback, useEffect, useMemo } from 'react'

import { TutorA2UISurface } from '@/components/a2ui/TutorA2UISurface'
import { TutorChatPanel } from '@/components/tutor-chat/TutorChatPanel'
import { VoiceShellBridge } from '@/components/voice/VoiceShellBridge'
import { tutorActionLabel } from '@/constants/tutor-actions'
import { useTutorA2UI } from '@/hooks/tutor/useTutorA2UI'
import { useTutorChat } from '@/hooks/tutor/useTutorChat'
import { useTutorTranscript } from '@/hooks/tutor/useTutorTranscript'
import { buildTutorSessionContext } from '@/lib/build-tutor-session-context'
import type { QuestionDetailResponse, TutorViewResponse } from '@/types/session-review'

interface SessionReviewTutorSectionProps {
  sessionId: string
  tutorView: TutorViewResponse
  detail: QuestionDetailResponse
  analyzing?: boolean
  onAnalyze?: () => void
}

export function SessionReviewTutorSection({
  sessionId,
  tutorView,
  detail,
  analyzing = false,
  onAnalyze,
}: SessionReviewTutorSectionProps) {
  const questionId = detail.package.question_id

  const { transcript, recentActions, appendTranscript, recordAction, syncAssistantMessage } =
    useTutorTranscript(questionId)

  const { isLoading, assistantPreview, dispatchMessage, chatError, stopGeneration } = useTutorChat({
    onUserDispatch: (content, source) => {
      appendTranscript({ role: 'user', content, source, ts: Date.now() })
    },
  })

  const { messages: a2uiMessages, dataModel: a2uiDataModel } = useTutorA2UI()

  const sessionContext = useMemo(
    () =>
      buildTutorSessionContext({
        sessionId,
        detail,
        tutorView,
        a2uiDataModel,
        recentActions,
        transcript,
      }),
    [sessionId, detail, tutorView, a2uiDataModel, recentActions, transcript],
  )

  useAgentContext({
    description: 'tutor_session_context',
    value: sessionContext as unknown as JsonSerializable,
  })

  useEffect(() => {
    syncAssistantMessage(assistantPreview, isLoading)
  }, [assistantPreview, isLoading, syncAssistantMessage])

  const handleSend = useCallback(
    (message: string) => {
      void dispatchMessage(message, 'text')
    },
    [dispatchMessage],
  )

  const handleAction = useCallback(
    (actionId: string) => {
      recordAction(actionId)
      void dispatchMessage(tutorActionLabel(actionId), 'action')
    },
    [dispatchMessage, recordAction],
  )

  const handleVoiceUtterance = useCallback(
    (message: string) => dispatchMessage(message, 'asr'),
    [dispatchMessage],
  )

  const handleBargeIn = useCallback(() => {
    stopGeneration()
  }, [stopGeneration])

  const chatDisabled = detail.tutor.analysis_status !== 'ready' || analyzing

  const voiceHandlers = useMemo(
    () => ({
      disabled: chatDisabled,
      onUserUtterance: handleVoiceUtterance,
      onBargeIn: handleBargeIn,
      assistantText: assistantPreview,
      chatLoading: isLoading,
    }),
    [assistantPreview, chatDisabled, handleBargeIn, handleVoiceUtterance, isLoading],
  )

  return (
    <>
      <VoiceShellBridge handlers={voiceHandlers} />
      <TutorA2UISurface
        package={detail.package}
        tutor={detail.tutor}
        messages={a2uiMessages}
        onAction={handleAction}
        onAnalyze={onAnalyze}
        analyzing={analyzing}
        chatLoading={isLoading}
      />
      {isLoading && assistantPreview ? (
        <div className="mt-2 rounded-lg border border-border/50 bg-background p-3 text-sm leading-relaxed">
          {assistantPreview}
        </div>
      ) : null}
      {chatError ? <p className="mt-2 text-sm text-destructive">{chatError}</p> : null}
      <TutorChatPanel disabled={chatDisabled} loading={isLoading} onSend={handleSend} />
    </>
  )
}
