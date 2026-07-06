import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { sessionReviewApi } from '@/services/sessionReviewApi'
import type {
  QuestionDetailResponse,
  TutorContent,
  TutorViewResponse,
} from '@/types/session-review'

function needsSse(tutor: TutorContent): boolean {
  return tutor.analysis_status === 'generating' || tutor.analysis_status === 'pending'
}

export interface SessionReviewStats {
  total: number
  wrong: number
  correct: number
  duration: number
}

export interface UseSessionReviewResult {
  tutorView: TutorViewResponse | null
  detail: QuestionDetailResponse | null
  currentQuestionId: string | null
  setCurrentQuestionId: (questionId: string) => void
  loading: boolean
  detailLoading: boolean
  analyzing: boolean
  prefetchingIds: Set<string>
  error: string | null
  detailError: string | null
  stats: SessionReviewStats | null
  sortedQuestions: TutorViewResponse['questions']
  currentIndex: number
  navigateQuestion: (delta: number) => void
  prefetchAnalyze: (questionId: string) => void
  handleAnalyze: () => void
}

export function useSessionReview(sessionId: string): UseSessionReviewResult {
  const [tutorView, setTutorView] = useState<TutorViewResponse | null>(null)
  const [detail, setDetail] = useState<QuestionDetailResponse | null>(null)
  const [currentQuestionId, setCurrentQuestionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [prefetchingIds, setPrefetchingIds] = useState<Set<string>>(() => new Set())
  const [error, setError] = useState<string | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const prefetchInflightRef = useRef<Set<string>>(new Set())

  const closeEventSource = useCallback(() => {
    eventSourceRef.current?.close()
    eventSourceRef.current = null
  }, [])

  const loadQuestion = useCallback(
    async (questionId: string) => {
      if (!sessionId) {
        return null
      }
      setDetailLoading(true)
      setDetailError(null)
      try {
        const data = await sessionReviewApi.getQuestion(sessionId, questionId)
        setDetail(data)
        return data
      } catch (err) {
        setDetailError(err instanceof Error ? err.message : '加载题目失败')
        return null
      } finally {
        setDetailLoading(false)
      }
    },
    [sessionId],
  )

  const openSse = useCallback(
    (questionId: string) => {
      if (!sessionId) {
        return
      }
      closeEventSource()
      eventSourceRef.current = sessionReviewApi.subscribeTutorEvents(
        sessionId,
        questionId,
        {
          onStatus: (status) => {
            setDetail((prev) =>
              prev
                ? {
                    ...prev,
                    tutor: {
                      ...prev.tutor,
                      analysis_status: status as TutorContent['analysis_status'],
                    },
                  }
                : prev,
            )
          },
          onTutor: (tutor) => {
            setAnalyzing(false)
            setDetail((prev) => (prev ? { ...prev, tutor } : prev))
            setTutorView((prev) =>
              prev
                ? {
                    ...prev,
                    questions: prev.questions.map((q) =>
                      q.question_id === questionId
                        ? {
                            ...q,
                            verdict: tutor.verdict,
                            summary: tutor.summary || q.summary,
                            analysis_status: tutor.analysis_status,
                            stale: Boolean(tutor.stale),
                          }
                        : q,
                    ),
                  }
                : prev,
            )
          },
          onError: (message) => {
            setAnalyzing(false)
            setDetailError(message)
          },
        },
      )
    },
    [closeEventSource, sessionId],
  )

  const prefetchAnalyze = useCallback(
    async (questionId: string) => {
      if (!sessionId || prefetchInflightRef.current.has(questionId)) {
        return
      }
      if (!tutorView?.analysis_policy.prefetch_on_select) {
        return
      }
      const summary = tutorView.questions.find((q) => q.question_id === questionId)
      if (!summary || summary.verdict !== 'wrong') {
        return
      }
      if (summary.analysis_status === 'generating' || summary.analysis_status === 'pending') {
        return
      }

      prefetchInflightRef.current.add(questionId)
      setPrefetchingIds((prev) => new Set(prev).add(questionId))
      try {
        await sessionReviewApi.analyze(sessionId, questionId)
        if (questionId === currentQuestionId) {
          setAnalyzing(true)
          openSse(questionId)
          setDetail((prev) =>
            prev
              ? {
                  ...prev,
                  tutor: { ...prev.tutor, analysis_status: 'generating' },
                }
              : prev,
          )
        }
        setTutorView((prev) =>
          prev
            ? {
                ...prev,
                questions: prev.questions.map((q) =>
                  q.question_id === questionId
                    ? { ...q, analysis_status: 'generating' as const }
                    : q,
                ),
              }
            : prev,
        )
      } catch (err) {
        if (questionId === currentQuestionId) {
          setDetailError(err instanceof Error ? err.message : '无法启动分析')
        }
      } finally {
        prefetchInflightRef.current.delete(questionId)
        setPrefetchingIds((prev) => {
          const next = new Set(prev)
          next.delete(questionId)
          return next
        })
      }
    },
    [
      currentQuestionId,
      openSse,
      sessionId,
      tutorView?.analysis_policy.prefetch_on_select,
      tutorView?.questions,
    ],
  )

  const handleAnalyze = useCallback(async () => {
    if (!sessionId || !currentQuestionId) {
      return
    }
    setAnalyzing(true)
    setDetailError(null)
    try {
      await sessionReviewApi.analyze(sessionId, currentQuestionId)
      openSse(currentQuestionId)
      setDetail((prev) =>
        prev
          ? {
              ...prev,
              tutor: { ...prev.tutor, analysis_status: 'generating' },
            }
          : prev,
      )
      setTutorView((prev) =>
        prev
          ? {
              ...prev,
              questions: prev.questions.map((q) =>
                q.question_id === currentQuestionId
                  ? { ...q, analysis_status: 'generating' as const }
                  : q,
              ),
            }
          : prev,
      )
    } catch (err) {
      setAnalyzing(false)
      setDetailError(err instanceof Error ? err.message : '无法启动分析')
    }
  }, [currentQuestionId, openSse, sessionId])

  useEffect(() => {
    if (!sessionId) {
      return
    }
    setLoading(true)
    setError(null)
    sessionReviewApi
      .getTutorView(sessionId)
      .then((view) => {
        setTutorView(view)
        const firstWrong = view.questions.find((q) => q.verdict === 'wrong')
        const firstSeg = view.timeline_index.segments[0]
        const initial =
          firstWrong?.question_id ?? firstSeg?.question_id ?? view.questions[0]?.question_id
        setCurrentQuestionId(initial ?? null)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [sessionId])

  useEffect(() => {
    if (!currentQuestionId) {
      return
    }
    closeEventSource()
    void loadQuestion(currentQuestionId).then((data) => {
      if (data && needsSse(data.tutor)) {
        openSse(currentQuestionId)
      }
    })
    return closeEventSource
  }, [closeEventSource, currentQuestionId, loadQuestion, openSse])

  const stats = useMemo((): SessionReviewStats | null => {
    if (!tutorView) {
      return null
    }
    const total = tutorView.questions.length
    const wrong = tutorView.questions.filter((q) => q.verdict === 'wrong').length
    const correct = tutorView.questions.filter((q) => q.verdict === 'correct').length
    return { total, wrong, correct, duration: tutorView.timeline_index.duration_ms }
  }, [tutorView])

  const sortedQuestions = useMemo(
    () => (tutorView ? [...tutorView.questions].sort((a, b) => a.number - b.number) : []),
    [tutorView],
  )

  const currentIndex = useMemo(
    () => sortedQuestions.findIndex((q) => q.question_id === currentQuestionId),
    [sortedQuestions, currentQuestionId],
  )

  const navigateQuestion = useCallback(
    (delta: number) => {
      if (currentIndex < 0) {
        return
      }
      const next = sortedQuestions[currentIndex + delta]
      if (next) {
        setCurrentQuestionId(next.question_id)
      }
    },
    [currentIndex, sortedQuestions],
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        navigateQuestion(-1)
      } else if (e.key === 'ArrowRight') {
        navigateQuestion(1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [navigateQuestion])

  return {
    tutorView,
    detail,
    currentQuestionId,
    setCurrentQuestionId,
    loading,
    detailLoading,
    analyzing,
    prefetchingIds,
    error,
    detailError,
    stats,
    sortedQuestions,
    currentIndex,
    navigateQuestion,
    prefetchAnalyze: (questionId: string) => {
      void prefetchAnalyze(questionId)
    },
    handleAnalyze,
  }
}
