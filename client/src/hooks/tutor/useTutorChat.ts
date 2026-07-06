import type { Message } from '@ag-ui/core'
import { useAgent, useCopilotKit, UseAgentUpdate } from '@copilotkit/react-core/v2'
import { useCallback, useMemo, useState } from 'react'

import { TUTOR_AGENT_ID } from '@/constants/copilot'
import type { TranscriptEntry } from '@/types/tutor-session-context'

export interface UseTutorChatOptions {
  onUserDispatch?: (content: string, source: TranscriptEntry['source']) => void
}

function messageTextContent(message: Message): string {
  if (!('content' in message)) {
    return ''
  }

  const { content } = message
  if (typeof content === 'string') {
    return content
  }

  if (!Array.isArray(content)) {
    return ''
  }

  return content
    .map((part) => {
      if (typeof part === 'string') {
        return part
      }
      if (part && typeof part === 'object' && 'type' in part && part.type === 'text' && 'text' in part) {
        return String(part.text ?? '')
      }
      return ''
    })
    .join('')
}

export function useTutorChat(options: UseTutorChatOptions = {}) {
  const { copilotkit } = useCopilotKit()
  const { agent } = useAgent({
    agentId: TUTOR_AGENT_ID,
    updates: [UseAgentUpdate.OnMessagesChanged, UseAgentUpdate.OnRunStatusChanged],
    throttleMs: 100,
  })
  const [chatError, setChatError] = useState<string | null>(null)

  const messages = agent.messages
  const isLoading = agent.isRunning

  const assistantPreview = useMemo(() => {
    const lastAssistant = [...messages].reverse().find((message) => message.role === 'assistant')
    if (!lastAssistant) {
      return ''
    }
    return messageTextContent(lastAssistant)
  }, [messages])

  const sendMessage = useCallback(
    async (message: { id: string; role: 'user'; content: string }) => {
      agent.addMessage({
        id: message.id,
        role: message.role,
        content: message.content,
      })
      await copilotkit.runAgent({ agent })
    },
    [agent, copilotkit],
  )

  const stopGeneration = useCallback(() => {
    agent.abortRun()
  }, [agent])

  const dispatchMessage = useCallback(
    async (content: string, source: TranscriptEntry['source']) => {
      setChatError(null)
      options.onUserDispatch?.(content, source)
      try {
        await sendMessage({
          id: crypto.randomUUID(),
          role: 'user',
          content,
        })
      } catch (err) {
        setChatError(err instanceof Error ? err.message : '对话失败')
      }
    },
    [options.onUserDispatch, sendMessage],
  )

  return {
    sendMessage,
    stopGeneration,
    isLoading,
    messages,
    assistantPreview,
    dispatchMessage,
    chatError,
    setChatError,
  }
}
