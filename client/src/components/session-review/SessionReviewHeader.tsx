import { ArrowLeft, CheckCircle2, Clock, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

import { QuestionNavBar } from '@/components/session-review/QuestionNavBar'
import { formatDurationMs } from '@/lib/timeline-utils'
import type { QuestionSummary } from '@/types/session-review'

interface SessionReviewHeaderProps {
  stats: {
    total: number
    correct: number
    wrong: number
    duration: number
  }
  questions: QuestionSummary[]
  currentQuestionId: string | null
  onSelectQuestion: (questionId: string) => void
  onPrefetchAnalyze?: (questionId: string) => void
  prefetchingIds?: ReadonlySet<string>
  onNavigate?: (delta: number) => void
  canNavigatePrev?: boolean
  canNavigateNext?: boolean
}

export function SessionReviewHeader({
  stats,
  questions,
  currentQuestionId,
  onSelectQuestion,
  onPrefetchAnalyze,
  prefetchingIds,
  onNavigate,
  canNavigatePrev,
  canNavigateNext,
}: SessionReviewHeaderProps) {
  const accuracy =
    stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/95 backdrop-blur-sm">
      <div className="session-review-shell py-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <Link
            to="/"
            className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="返回书架"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
          </Link>
          <h1 className="text-lg font-semibold tracking-tight">作业讲解回顾</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span className="tabular-nums">共 {stats.total} 题</span>
            <span className="inline-flex items-center gap-1 text-emerald-700">
              <CheckCircle2 className="h-3 w-3" aria-hidden />
              {stats.correct} 正确
            </span>
            <span className="inline-flex items-center gap-1 text-amber-800">
              <XCircle className="h-3 w-3" aria-hidden />
              {stats.wrong} 有误
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" aria-hidden />
              {formatDurationMs(stats.duration)}
            </span>
            <span className="text-foreground/80">正确率 {accuracy}%</span>
          </div>
        </div>

        <QuestionNavBar
          questions={questions}
          currentQuestionId={currentQuestionId}
          onSelectQuestion={onSelectQuestion}
          onPrefetchAnalyze={onPrefetchAnalyze}
          prefetchingIds={prefetchingIds}
          onNavigate={onNavigate}
          canNavigatePrev={canNavigatePrev}
          canNavigateNext={canNavigateNext}
        />
      </div>
    </header>
  )
}
