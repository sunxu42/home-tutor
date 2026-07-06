import type { A2UIMessage } from '@/types/a2ui'
import type { TutorContent } from '@/types/session-review'

export function fingerprintA2UIMessages(messages: A2UIMessage[]): string {
  return JSON.stringify(messages)
}

export function fingerprintTutorSeed(tutor: TutorContent, studentAnswer: string): string {
  return JSON.stringify({
    analysis_status: tutor.analysis_status,
    summary: tutor.summary,
    verdict: tutor.verdict,
    reference_answer: tutor.reference_answer,
    explanation_paragraphs: tutor.explanation_paragraphs,
    actions: tutor.actions,
    studentAnswer,
  })
}
