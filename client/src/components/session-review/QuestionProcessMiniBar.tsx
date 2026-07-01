import { useMemo, useState } from 'react'

import { mapAnswerToQuestionPercent } from '@/lib/timeline-utils'
import type { QuestionProcessPackage } from '@/types/session-review'
import { ReviewSection } from '@/components/session-review/ReviewSection'
import { cn } from '@/lib/utils'

interface QuestionProcessMiniBarProps {
  package: QuestionProcessPackage
}

export function QuestionProcessMiniBar({ package: pkg }: QuestionProcessMiniBarProps) {
  const timeline = pkg.answer_timeline
  const idlePeriods = pkg.process_metrics.idle_periods_ms ?? []
  const stuck = pkg.process_metrics.stuck ?? false
  const [activeIndex, setActiveIndex] = useState(() =>
    timeline.length > 0 ? timeline.length - 1 : 0,
  )

  const activeEntry = timeline[activeIndex]

  const dots = useMemo(
    () =>
      timeline.map((entry, index) => ({
        index,
        percent: mapAnswerToQuestionPercent(entry.t_offset_ms, pkg.focus_segments),
        label: entry.kind === 'appeared' ? '首次' : entry.kind === 'changed' ? '修改' : '擦除',
      })),
    [timeline, pkg.focus_segments],
  )

  const idleBands = useMemo(
    () =>
      idlePeriods.map((idle, index) => {
        const start = mapAnswerToQuestionPercent(idle.start_ms, pkg.focus_segments)
        const end = mapAnswerToQuestionPercent(idle.end_ms, pkg.focus_segments)
        return {
          index,
          left: Math.min(start, end),
          width: Math.max(2, Math.abs(end - start)),
        }
      }),
    [idlePeriods, pkg.focus_segments],
  )

  if (timeline.length === 0) {
    return (
      <ReviewSection title="书写过程">
        <p className="text-sm text-muted-foreground">暂无识别到的书写过程。</p>
      </ReviewSection>
    )
  }

  return (
    <ReviewSection title="书写过程">
      {stuck ? (
        <p className="mb-2 text-xs text-amber-800">停留较久，可能卡壳（灰色区间为停笔）</p>
      ) : null}

      <div className="relative mb-3 h-7 rounded-full bg-muted/50">
        <div className="absolute inset-x-2 top-1/2 h-px -translate-y-1/2 bg-border" />
        {idleBands.map((band) => (
          <div
            key={`idle-${band.index}`}
            className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-muted-foreground/25"
            style={{
              left: `calc(${Math.max(4, Math.min(92, band.left))}% + 0.25rem)`,
              width: `${Math.min(band.width, 30)}%`,
            }}
            title="停笔"
          />
        ))}
        {dots.map((dot) => (
          <button
            key={`${dot.index}-${dot.percent}`}
            type="button"
            className={cn(
              'absolute top-1/2 z-10 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 cursor-pointer rounded-full border-2 transition-colors',
              activeIndex === dot.index
                ? 'border-primary bg-primary'
                : 'border-muted-foreground/50 bg-background hover:border-primary',
            )}
            style={{ left: `${Math.max(4, Math.min(96, dot.percent))}%` }}
            title={dot.label}
            onClick={() => setActiveIndex(dot.index)}
            aria-label={`步骤 ${dot.index + 1}：${dot.label}`}
          />
        ))}
      </div>

      <div className="text-sm">
        {activeEntry ? (
          <>
            <span className="text-xs text-muted-foreground">
              {activeIndex + 1}/{timeline.length} · {activeEntry.kind}
            </span>
            <p className="mt-0.5 font-medium">{activeEntry.text}</p>
            {activeEntry.prev_text ? (
              <p className="mt-0.5 text-xs text-muted-foreground">上一版：{activeEntry.prev_text}</p>
            ) : null}
          </>
        ) : null}
      </div>
    </ReviewSection>
  )
}
