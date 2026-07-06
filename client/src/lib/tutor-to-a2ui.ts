import { HOME_TUTOR_CATALOG_ID, TUTOR_SURFACE_ID } from '@/components/a2ui/definitions'
import type { TutorContent } from '@/types/session-review'
import type { A2UIComponent, A2UIMessage } from '@/types/a2ui'

export function tutorContentToA2UI(
  tutor: TutorContent,
  options?: { studentAnswer?: string },
  surfaceId = TUTOR_SURFACE_ID,
): A2UIMessage[] {
  const components: A2UIComponent[] = tutor.explanation_paragraphs.map((paragraph, index) => ({
    id: `seed-text-${index + 1}`,
    component: 'TutorText',
    text: paragraph,
  }))

  if (tutor.reference_answer) {
    components.push({
      id: 'seed-compare',
      component: 'AnswerCompare',
      student: options?.studentAnswer ?? '',
      reference: tutor.reference_answer,
    })
  }

  for (const [index, action] of (tutor.actions ?? []).entries()) {
    if (!action.enabled) {
      continue
    }
    components.push({
      id: `seed-action-${index + 1}`,
      component: 'ActionChip',
      actionId: action.id,
      label: action.label,
    })
  }

  return [
    { version: '0.9', createSurface: { surfaceId, catalogId: HOME_TUTOR_CATALOG_ID } },
    { version: '0.9', updateComponents: { surfaceId, components } },
    {
      version: '0.9',
      updateDataModel: { surfaceId, path: '/', value: { seeded: true } },
    },
  ]
}
