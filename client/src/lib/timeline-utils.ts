import type { FocusSegment, TimelineSegment } from '@/types/session-review'

export function findSegmentAtTime(
  ms: number,
  segments: TimelineSegment[],
): TimelineSegment | null {
  if (segments.length === 0) {
    return null
  }

  for (const seg of segments) {
    if (ms >= seg.start_ms && ms <= seg.end_ms) {
      return seg
    }
  }

  let nearest: TimelineSegment | null = null
  for (const seg of segments) {
    if (seg.end_ms <= ms) {
      if (!nearest || seg.end_ms > nearest.end_ms) {
        nearest = seg
      }
    }
  }

  if (nearest) {
    return nearest
  }

  return segments.reduce((a, b) => (a.start_ms < b.start_ms ? a : b))
}

export function msToClickPosition(ms: number, durationMs: number, widthPx: number): number {
  if (durationMs <= 0) {
    return 0
  }
  return (ms / durationMs) * widthPx
}

export function clickPositionToMs(x: number, widthPx: number, durationMs: number): number {
  if (widthPx <= 0) {
    return 0
  }
  const ratio = Math.min(1, Math.max(0, x / widthPx))
  return Math.round(ratio * durationMs)
}

export function getQuestionTimeBounds(focusSegments: FocusSegment[]): {
  startMs: number
  endMs: number
} {
  if (focusSegments.length === 0) {
    return { startMs: 0, endMs: 1 }
  }
  const startMs = Math.min(...focusSegments.map((s) => s.start_ms))
  const endMs = Math.max(...focusSegments.map((s) => s.end_ms))
  return { startMs, endMs: Math.max(endMs, startMs + 1) }
}

export function mapAnswerToQuestionPercent(
  tOffsetMs: number,
  focusSegments: FocusSegment[],
): number {
  const { startMs, endMs } = getQuestionTimeBounds(focusSegments)
  const span = endMs - startMs
  if (span <= 0) {
    return 0
  }
  return Math.min(100, Math.max(0, ((tOffsetMs - startMs) / span) * 100))
}

export function formatDurationMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000)
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  return `${min}:${sec.toString().padStart(2, '0')}`
}
