/** Maps A2UI action ids to user-facing chat messages. */
export const TUTOR_ACTION_LABELS: Record<string, string> = {
  explain_more: '请详细讲讲',
  give_hint: '给我一个提示',
  next_question: '下一题',
}

export function tutorActionLabel(actionId: string): string {
  return TUTOR_ACTION_LABELS[actionId] ?? actionId
}
