import type { ErrorCategory } from '@/types/session-review'
import { cn } from '@/lib/utils'

const ERROR_LABELS: Record<ErrorCategory, string> = {
  correct: '正确',
  concept_error: '思路问题',
  calculation_error: '计算失误',
  incomplete: '未完成',
  unknown: '待确认',
}

export function VerdictBadge({ verdict }: { verdict: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
        verdict === 'correct' && 'bg-emerald-100 text-emerald-800',
        verdict === 'wrong' && 'bg-amber-100 text-amber-900',
        verdict === 'unknown' && 'bg-muted text-muted-foreground',
      )}
    >
      {verdict === 'correct' ? '正确' : verdict === 'wrong' ? '有误' : '待确认'}
    </span>
  )
}

export function ErrorCategoryBadge({ category }: { category: ErrorCategory }) {
  return (
    <span className="inline-flex items-center rounded bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-900">
      {ERROR_LABELS[category]}
    </span>
  )
}

export function FixtureBadge() {
  return (
    <span className="inline-flex items-center rounded bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-900">
      示例讲解
    </span>
  )
}
