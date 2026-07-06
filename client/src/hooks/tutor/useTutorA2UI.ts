import { useAgent, UseAgentUpdate } from '@copilotkit/react-core/v2'
import { useMemo } from 'react'

import { TUTOR_AGENT_ID } from '@/constants/copilot'
import { parseA2UIDataModel, parseA2UIMessages } from '@/protocol/a2ui'
import type { A2UIMessage } from '@/types/a2ui'

interface TutorAgentState {
  a2ui_messages?: unknown
  a2ui_data_model?: unknown
}

export function useTutorA2UI(): {
  messages: A2UIMessage[]
  dataModel: Record<string, unknown>
} {
  const { agent } = useAgent({
    agentId: TUTOR_AGENT_ID,
    updates: [UseAgentUpdate.OnStateChanged],
    throttleMs: 100,
  })

  const state = agent.state as TutorAgentState | undefined

  const a2uiMessagesKey = useMemo(
    () => JSON.stringify(state?.a2ui_messages ?? null),
    [state?.a2ui_messages],
  )

  const a2uiDataModelKey = useMemo(
    () => JSON.stringify(state?.a2ui_data_model ?? null),
    [state?.a2ui_data_model],
  )

  const messages = useMemo(
    () => parseA2UIMessages(state?.a2ui_messages),
    [a2uiMessagesKey],
  )

  const dataModel = useMemo(
    () => parseA2UIDataModel(state?.a2ui_data_model),
    [a2uiDataModelKey],
  )

  return { messages, dataModel }
}
