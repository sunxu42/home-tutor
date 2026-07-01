import { CheckCircle2, Circle } from 'lucide-react'

import type { ChoiceOption } from '@/types/session-review'
import { cn } from '@/lib/utils'

interface ChoiceOptionsListProps {
  options: ChoiceOption[]
  studentAnswer: string
  referenceAnswer: string
}

function normalizeKey(text: string): string {
  return text.trim().toUpperCase().charAt(0)
}

export function ChoiceOptionsList({
  options,
  studentAnswer,
  referenceAnswer,
}: ChoiceOptionsListProps) {
  const studentKey = normalizeKey(studentAnswer)
  const referenceKey = normalizeKey(referenceAnswer)

  return (
    <ul className="space-y-1.5">
      {options.map((option) => {
        const isStudent = option.key === studentKey
        const isReference = option.key === referenceKey
        const isCorrectPick = isStudent && isReference

        return (
          <li
            key={option.key}
            className={cn(
              'flex items-start gap-2 rounded-md px-2 py-1.5 text-sm leading-relaxed',
              isCorrectPick && 'bg-emerald-50',
              isStudent && !isReference && 'bg-amber-50',
              isReference && !isStudent && 'bg-emerald-50/60',
              !isStudent && !isReference && 'bg-transparent',
            )}
          >
            <span className="mt-0.5 shrink-0 text-primary">
              {isStudent || isReference ? (
                <CheckCircle2 className="h-4 w-4" aria-hidden />
              ) : (
                <Circle className="h-4 w-4 text-muted-foreground/50" aria-hidden />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <p>
                <span className="font-semibold text-foreground">{option.key}.</span>{' '}
                {option.text}
              </p>
              {(isStudent || isReference) && (
                <p className="mt-1 text-xs text-muted-foreground">
                  {isCorrectPick && '你的选择 · 答对了'}
                  {isStudent && !isReference && '你的选择'}
                  {isReference && !isStudent && '参考答案'}
                </p>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
