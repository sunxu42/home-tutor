import { lazy, Suspense, type ReactNode } from 'react'

import { TUTOR_AGENT_ID } from '@/constants/copilot'

const COPILOT_RUNTIME_URL = import.meta.env.VITE_COPILOT_RUNTIME_URL ?? '/api/copilotkit'
const COPILOT_LICENSE_KEY = import.meta.env.VITE_COPILOTKIT_LICENSE_KEY

const CopilotKitShell = lazy(async () => {
  const [{ CopilotKit }] = await Promise.all([
    import('@copilotkit/react-core/v2'),
    import('@copilotkit/react-core/v2/styles.css'),
  ])

  return {
    default: function CopilotKitShell({
      children,
      threadId,
    }: {
      children: ReactNode
      threadId?: string
    }) {
      return (
        <CopilotKit
          runtimeUrl={COPILOT_RUNTIME_URL}
          agent={TUTOR_AGENT_ID}
          useSingleEndpoint={false}
          publicLicenseKey={COPILOT_LICENSE_KEY || undefined}
          threadId={threadId}
        >
          {children}
        </CopilotKit>
      )
    },
  }
})

function CopilotKitFallback() {
  return (
    <div className="flex min-h-[12rem] items-center justify-center rounded-lg border border-border/60 bg-muted/20">
      <p className="text-sm text-muted-foreground">正在加载 AI 助手...</p>
    </div>
  )
}

export function CopilotAppProvider({
  children,
  threadId,
}: {
  children: ReactNode
  threadId?: string
}) {
  return (
    <Suspense fallback={<CopilotKitFallback />}>
      <CopilotKitShell threadId={threadId}>{children}</CopilotKitShell>
    </Suspense>
  )
}
