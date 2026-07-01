import type { QuestionType } from '@/types/session-review'

export const QUESTION_TYPE_ORDER: QuestionType[] = [
  'fill_blank',
  'multiple_choice',
  'calculation',
  'word_problem',
  'unknown',
]

export const QUESTION_TYPE_GROUP_LABEL: Record<QuestionType, string> = {
  fill_blank: '填空',
  multiple_choice: '选择',
  calculation: '计算',
  word_problem: '应用',
  unknown: '其他',
}

export const QUESTION_TYPE_ABBR: Record<QuestionType, string> = {
  fill_blank: '填',
  multiple_choice: '选',
  calculation: '算',
  word_problem: '应',
  unknown: '·',
}

/** 题型分组左侧色条，与正误色独立 */
export const QUESTION_TYPE_ACCENT: Record<QuestionType, string> = {
  fill_blank: 'border-l-sky-400',
  multiple_choice: 'border-l-violet-400',
  calculation: 'border-l-blue-400',
  word_problem: 'border-l-rose-400',
  unknown: 'border-l-muted-foreground/40',
}

export function normalizeQuestionType(type?: string): QuestionType {
  if (
    type === 'fill_blank' ||
    type === 'multiple_choice' ||
    type === 'calculation' ||
    type === 'word_problem'
  ) {
    return type
  }
  return 'unknown'
}
