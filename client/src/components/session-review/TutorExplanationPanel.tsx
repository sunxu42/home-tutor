import { Loader2, Sparkles } from 'lucide-react'

import {
  ErrorCategoryBadge,
  FixtureBadge,
  VerdictBadge,
} from '@/components/session-review/SessionReviewBadges'
import type { QuestionProcessPackage, TutorContent } from '@/types/session-review'
import { cn } from '@/lib/utils'

interface TutorExplanationPanelProps {
  package: QuestionProcessPackage
  tutor: TutorContent
  onAnalyze?: () => void
  analyzing?: boolean
}

export function TutorExplanationPanel({
  package: pkg,
  tutor,
  onAnalyze,
  analyzing = false,
}: TutorExplanationPanelProps) {
  const packageUpdating = pkg.status === 'updating'
  const analysisLoading =
    analyzing ||
    tutor.analysis_status === 'generating' ||
    tutor.analysis_status === 'pending'
  const isFixtureTutor = tutor.analysis_status === 'ready' && Boolean(tutor.model?.startsWith('mock'))
  const showAnalyzeButton = Boolean(onAnalyze) && !analysisLoading
  const analyzeLabel =
    tutor.analysis_status === 'missing' || tutor.analysis_status === 'failed' || isFixtureTutor
      ? 'AI 分析'
      : '重新分析'
  const showContent = tutor.analysis_status === 'ready' && !analysisLoading

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b border-border/50 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden />
            <h2 className="text-base font-semibold">AI 讲解</h2>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {isFixtureTutor ? <FixtureBadge /> : null}
            {tutor.error_classification ? (
              <ErrorCategoryBadge category={tutor.error_classification.category} />
            ) : null}
            <VerdictBadge verdict={tutor.verdict} />
          </div>
        </div>
        {tutor.summary ? (
          <p className="mt-2 text-sm font-medium leading-snug">{tutor.summary}</p>
        ) : null}
        {tutor.process_comment ? (
          <p className="mt-1 text-xs text-muted-foreground">{tutor.process_comment}</p>
        ) : null}
        {showAnalyzeButton ? (
          <button
            type="button"
            onClick={onAnalyze}
            disabled={analyzing}
            className="mt-2 inline-flex cursor-pointer items-center gap-2 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {analyzing ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
            {analyzeLabel}
          </button>
        ) : null}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pt-3">
        {packageUpdating || analysisLoading ? (
          <div className="space-y-2 py-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden />
              AI 正在分析…
            </div>
            <div className="space-y-1.5">
              <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
              <div className="h-3 w-full animate-pulse rounded bg-muted" />
            </div>
          </div>
        ) : null}

        {tutor.analysis_status === 'failed' ? (
          <p className="text-sm text-destructive">{tutor.error ?? '分析失败，请稍后重试。'}</p>
        ) : null}

        {showContent ? (
          <>
            <div className="space-y-2">
              {tutor.explanation_paragraphs.map((paragraph) => (
                <p key={paragraph} className="text-sm leading-relaxed text-foreground/90">
                  {paragraph}
                </p>
              ))}
            </div>
            {tutor.actions && tutor.actions.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 border-t border-border/50 pt-3">
                {tutor.actions.map((action) => (
                  <button
                    key={action.id}
                    type="button"
                    disabled={!action.enabled}
                    className={cn(
                      'rounded-md px-2.5 py-1 text-xs transition-colors',
                      action.enabled
                        ? 'cursor-pointer bg-muted/80 text-foreground hover:bg-muted'
                        : 'cursor-not-allowed text-muted-foreground',
                    )}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            ) : null}
          </>
        ) : null}

        {tutor.analysis_status === 'missing' && !onAnalyze ? (
          <p className="text-sm text-muted-foreground">尚未生成 AI 讲解。</p>
        ) : null}
      </div>
    </div>
  )
}
