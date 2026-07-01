import { useMemo, useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Filter,
  Loader2,
} from 'lucide-react'

import {
  normalizeQuestionType,
  QUESTION_TYPE_ABBR,
  QUESTION_TYPE_ACCENT,
  QUESTION_TYPE_GROUP_LABEL,
  QUESTION_TYPE_ORDER,
} from '@/lib/question-type-utils'
import type { AnalysisStatus, QuestionSummary } from '@/types/session-review'
import { cn } from '@/lib/utils'

interface QuestionNavBarProps {
  questions: QuestionSummary[]
  currentQuestionId: string | null
  onSelectQuestion: (questionId: string) => void
  onPrefetchAnalyze?: (questionId: string) => void
  prefetchingIds?: ReadonlySet<string>
  onNavigate?: (delta: number) => void
  canNavigatePrev?: boolean
  canNavigateNext?: boolean
}

const ANALYSIS_LABELS: Record<AnalysisStatus, string> = {
  missing: '未分析',
  pending: '排队中',
  generating: '分析中',
  ready: '已讲解',
  failed: '分析失败',
}

function verdictLabel(verdict: string): string {
  if (verdict === 'correct') return '正确'
  if (verdict === 'wrong') return '有误'
  return '待确认'
}

function navButtonClass(verdict: string, selected: boolean): string {
  return cn(
    'relative h-7 min-w-7 cursor-pointer rounded px-1.5 text-xs font-medium tabular-nums transition-colors',
    verdict === 'correct' && 'bg-emerald-100/90 text-emerald-900 hover:bg-emerald-200/80',
    verdict === 'wrong' && 'bg-amber-100/90 text-amber-900 hover:bg-amber-200/80',
    verdict !== 'correct' &&
      verdict !== 'wrong' &&
      'bg-muted/70 text-muted-foreground hover:bg-muted',
    selected && 'ring-2 ring-primary ring-offset-1',
  )
}

export function QuestionNavBar({
  questions,
  currentQuestionId,
  onSelectQuestion,
  onPrefetchAnalyze,
  prefetchingIds,
  onNavigate,
  canNavigatePrev = false,
  canNavigateNext = false,
}: QuestionNavBarProps) {
  const [wrongOnly, setWrongOnly] = useState(false)
  const [hoveredQuestionId, setHoveredQuestionId] = useState<string | null>(null)

  const sortedQuestions = useMemo(
    () => [...questions].sort((a, b) => a.number - b.number),
    [questions],
  )

  const visibleQuestions = useMemo(
    () => (wrongOnly ? sortedQuestions.filter((q) => q.verdict === 'wrong') : sortedQuestions),
    [sortedQuestions, wrongOnly],
  )

  const grouped = useMemo(() => {
    const buckets = new Map(
      QUESTION_TYPE_ORDER.map((type) => [type, [] as QuestionSummary[]]),
    )
    for (const question of visibleQuestions) {
      const type = normalizeQuestionType(question.question_type)
      buckets.get(type)?.push(question)
    }
    return QUESTION_TYPE_ORDER.map((type) => ({
      type,
      items: buckets.get(type) ?? [],
    })).filter((group) => group.items.length > 0)
  }, [visibleQuestions])

  const hoveredQuestion = hoveredQuestionId
    ? sortedQuestions.find((q) => q.question_id === hoveredQuestionId)
    : undefined

  const handleSelect = (questionId: string) => {
    onSelectQuestion(questionId)
    onPrefetchAnalyze?.(questionId)
  }

  return (
    <div className="relative border-t border-border/50 pt-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">按题型浏览 · 悬停查看题干</p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setWrongOnly((v) => !v)}
            className={cn(
              'inline-flex cursor-pointer items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors',
              wrongOnly
                ? 'bg-amber-100 text-amber-900'
                : 'text-muted-foreground hover:bg-muted/80 hover:text-foreground',
            )}
            aria-pressed={wrongOnly}
          >
            <Filter className="h-3 w-3" aria-hidden />
            只看错题
          </button>
          {onNavigate ? (
            <>
              <button
                type="button"
                disabled={!canNavigatePrev}
                onClick={() => onNavigate(-1)}
                className="inline-flex h-7 w-7 cursor-pointer items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="上一题"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                disabled={!canNavigateNext}
                onClick={() => onNavigate(1)}
                className="inline-flex h-7 w-7 cursor-pointer items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="下一题"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </>
          ) : null}
        </div>
      </div>

      {hoveredQuestion ? (
        <div
          className="pointer-events-none absolute left-0 top-full z-50 mt-1 max-w-md rounded-lg border border-border/80 bg-popover px-3 py-2 shadow-lg"
          role="tooltip"
        >
          <p className="text-xs font-medium">
            第 {hoveredQuestion.number} 题 ·{' '}
            {QUESTION_TYPE_GROUP_LABEL[normalizeQuestionType(hoveredQuestion.question_type)]} ·{' '}
            {verdictLabel(hoveredQuestion.verdict)}
          </p>
          {hoveredQuestion.prompt_preview ? (
            <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
              {hoveredQuestion.prompt_preview}
            </p>
          ) : null}
          {hoveredQuestion.answer_preview ? (
            <p className="mt-1 text-xs">
              <span className="text-muted-foreground">你的答案：</span>
              {hoveredQuestion.answer_preview}
            </p>
          ) : null}
          <p className="mt-1 text-[10px] text-muted-foreground">
            {ANALYSIS_LABELS[hoveredQuestion.analysis_status]}
            {prefetchingIds?.has(hoveredQuestion.question_id) ? ' · 解析中' : ''}
          </p>
        </div>
      ) : null}

      {visibleQuestions.length === 0 ? (
        <p className="py-2 text-center text-xs text-muted-foreground">没有错题</p>
      ) : (
        <div
          className="flex flex-wrap items-center gap-x-3 gap-y-2"
          role="tablist"
          aria-label="题目导航"
        >
          {grouped.map((group, groupIndex) => (
            <div key={group.type} className="flex items-center gap-1.5">
              {groupIndex > 0 ? (
                <span className="mr-1 hidden h-4 w-px bg-border sm:inline" aria-hidden />
              ) : null}
              <span
                className={cn(
                  'shrink-0 border-l-2 pl-1 text-[10px] font-medium text-muted-foreground',
                  QUESTION_TYPE_ACCENT[group.type],
                )}
                title={QUESTION_TYPE_GROUP_LABEL[group.type]}
              >
                {QUESTION_TYPE_GROUP_LABEL[group.type]}
              </span>
              <div className="flex flex-wrap gap-0.5">
                {group.items.map((question) => {
                  const selected = question.question_id === currentQuestionId
                  const prefetching = prefetchingIds?.has(question.question_id) ?? false
                  const type = normalizeQuestionType(question.question_type)

                  return (
                    <button
                      key={question.question_id}
                      type="button"
                      role="tab"
                      aria-selected={selected}
                      aria-label={`第 ${question.number} 题，${QUESTION_TYPE_GROUP_LABEL[type]}，${verdictLabel(question.verdict)}`}
                      className={cn(
                        navButtonClass(question.verdict, selected),
                        'border-l-2',
                        QUESTION_TYPE_ACCENT[type],
                        prefetching && 'opacity-60',
                      )}
                      onMouseEnter={() => setHoveredQuestionId(question.question_id)}
                      onMouseLeave={() => setHoveredQuestionId(null)}
                      onFocus={() => setHoveredQuestionId(question.question_id)}
                      onBlur={() => setHoveredQuestionId(null)}
                      onClick={() => handleSelect(question.question_id)}
                    >
                      {prefetching ? (
                        <Loader2 className="mx-auto h-3 w-3 animate-spin" aria-hidden />
                      ) : (
                        <>
                          <span className="sr-only">{QUESTION_TYPE_ABBR[type]}</span>
                          {question.number}
                        </>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
