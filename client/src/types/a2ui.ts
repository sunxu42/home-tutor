export interface A2UIComponent {
  id: string
  component: string
  text?: string
  student?: string
  reference?: string
  items?: string[]
  actionId?: string
  label?: string
  title?: string
  expanded?: boolean
  frameId?: string
  imageUrl?: string
}

export interface A2UIMessage {
  version?: string
  createSurface?: { surfaceId: string; catalogId: string }
  updateComponents?: { surfaceId: string; components: A2UIComponent[] }
  updateDataModel?: { surfaceId: string; path: string; value: Record<string, unknown> }
}

export interface AgUiEvent {
  type: string
  messageId?: string
  role?: string
  delta?: string
  name?: string
  value?: unknown
}
