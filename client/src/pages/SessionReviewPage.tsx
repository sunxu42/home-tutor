import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { QuestionContextPanel } from '@/components/session-review/QuestionContextPanel'
import { SessionReviewHeader } from '@/components/session-review/SessionReviewHeader'
import { TutorExplanationPanel } from '@/components/session-review/TutorExplanationPanel'
import { sessionReviewApi } from '@/services/sessionReviewApi'
import type {
  QuestionDetailResponse,
  TutorContent,
  TutorViewResponse,
} from '@/types/session-review'

function needsSse(tutor: TutorContent): boolean {
  return tutor.analysis_status === 'generating' || tutor.analysis_status === 'pending'
}

export function SessionReviewPage() {
  const { sessionId = '' } = useParams()
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
        return
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
                    tutor: { ...prev.tutor, analysis_status: status as TutorContent['analysis_status'] },
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
    [currentQuestionId, openSse, sessionId, tutorView?.analysis_policy.prefetch_on_select, tutorView?.questions],
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

  const stats = useMemo(() => {
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

  if (loading) {
    return (
      <div className="session-review flex min-h-svh items-center justify-center text-muted-foreground">
        加载讲解数据…
      </div>
    )
  }

  if (error || !tutorView || !stats) {
    return (
      <div className="session-review flex min-h-svh flex-col items-center justify-center gap-4 px-4">
        <p className="text-destructive">{error ?? '无法加载会话'}</p>
        <Link
          to="/"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          返回书架
        </Link>
      </div>
    )
  }

  return (
    <div className="session-review flex min-h-svh flex-col bg-background">
      <a
        href="#session-review-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        跳到主要内容
      </a>

      <SessionReviewHeader
        stats={stats}
        questions={tutorView.questions}
        currentQuestionId={currentQuestionId}
        onSelectQuestion={setCurrentQuestionId}
        onPrefetchAnalyze={
          tutorView.analysis_policy.prefetch_on_select
            ? (questionId) => {
                void prefetchAnalyze(questionId)
              }
            : undefined
        }
        prefetchingIds={prefetchingIds}
        onNavigate={navigateQuestion}
        canNavigatePrev={currentIndex > 0}
        canNavigateNext={currentIndex >= 0 && currentIndex < sortedQuestions.length - 1}
      />

      <main id="session-review-main" className="flex-1">
        <div className="session-review-shell">
          {detailError ? (
            <p className="py-2 text-sm text-destructive">{detailError}</p>
          ) : null}

          {detailLoading || !detail ? (
            <div className="session-review-layout">
              <div className="session-review-question h-64 animate-pulse bg-muted/40" />
              <div className="session-review-tutor h-64 animate-pulse bg-muted/30" />
            </div>
          ) : (
            <div className="session-review-layout">
              <div className="session-review-question">
                <QuestionContextPanel package={detail.package} tutor={detail.tutor} />
              </div>
              <section className="session-review-tutor">
                <TutorExplanationPanel
                  package={detail.package}
                  tutor={detail.tutor}
                  analyzing={analyzing}
                  onAnalyze={handleAnalyze}
                />
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
