import type { QuestionType } from '@/types/session-review'
import { cn } from '@/lib/utils'

const TYPE_LABELS: Record<QuestionType, string> = {
  fill_blank: '填空题',
  multiple_choice: '选择题',
  calculation: '计算题',
  word_problem: '应用题',
  unknown: '其他',
}

const TYPE_TONES: Record<QuestionType, string> = {
  fill_blank: 'bg-sky-100 text-sky-900',
  multiple_choice: 'bg-violet-100 text-violet-900',
  calculation: 'bg-blue-100 text-blue-900',
  word_problem: 'bg-rose-100 text-rose-900',
  unknown: 'bg-muted text-muted-foreground',
}

export function QuestionTypeBadge({ type }: { type: QuestionType }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium',
        TYPE_TONES[type],
      )}
    >
      {TYPE_LABELS[type]}
    </span>
  )
}
