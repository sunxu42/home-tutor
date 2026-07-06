import { z } from 'zod'

import type { A2UIComponent, A2UIMessage } from '@/types/a2ui'

const A2UIComponentSchema: z.ZodType<A2UIComponent> = z.object({
  id: z.string(),
  component: z.string(),
  text: z.string().optional(),
  student: z.string().optional(),
  reference: z.string().optional(),
  items: z.array(z.string()).optional(),
  actionId: z.string().optional(),
  label: z.string().optional(),
  title: z.string().optional(),
  expanded: z.boolean().optional(),
  frameId: z.string().optional(),
  imageUrl: z.string().optional(),
})

const A2UIMessageSchema: z.ZodType<A2UIMessage> = z.object({
  version: z.string().optional(),
  createSurface: z
    .object({
      surfaceId: z.string(),
      catalogId: z.string(),
    })
    .optional(),
  updateComponents: z
    .object({
      surfaceId: z.string(),
      components: z.array(A2UIComponentSchema),
    })
    .optional(),
  updateDataModel: z
    .object({
      surfaceId: z.string(),
      path: z.string(),
      value: z.record(z.unknown()),
    })
    .optional(),
})

export const A2UIMessagesSchema = z.array(A2UIMessageSchema)

const A2UIDataModelSchema = z.record(z.unknown())

export function parseA2UIMessages(raw: unknown): A2UIMessage[] {
  const result = A2UIMessagesSchema.safeParse(raw)
  return result.success ? result.data : []
}

export function parseA2UIDataModel(raw: unknown): Record<string, unknown> {
  const result = A2UIDataModelSchema.safeParse(raw)
  return result.success ? result.data : {}
}
