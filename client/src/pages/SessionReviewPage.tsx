import { Link, useParams } from 'react-router-dom'

import { QuestionContextPanel } from '@/components/session-review/QuestionContextPanel'
import { SessionReviewHeader } from '@/components/session-review/SessionReviewHeader'
import { SessionReviewTutorSection } from '@/components/session-review/SessionReviewTutorSection'
import { useSessionReview } from '@/hooks/useSessionReview'
import { CopilotAppProvider } from '@/providers/CopilotAppProvider'
import { VoiceShellRoot } from '@/providers/VoiceShellRoot'

export function SessionReviewPage() {
  const { sessionId = '' } = useParams()
  const {
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
    prefetchAnalyze,
    handleAnalyze,
  } = useSessionReview(sessionId)

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

  const copilotThreadId =
    currentQuestionId != null ? `${sessionId}:${currentQuestionId}` : undefined
  const detailReady =
    detail != null && detail.package.question_id === currentQuestionId

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
          tutorView.analysis_policy.prefetch_on_select ? prefetchAnalyze : undefined
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

          <div className="session-review-layout">
            <div className="session-review-question">
              {detailLoading || !detail ? (
                <div className="h-64 animate-pulse rounded-lg bg-muted/40" aria-busy="true" />
              ) : (
                <QuestionContextPanel package={detail.package} tutor={detail.tutor} />
              )}
            </div>

            <section className="session-review-tutor">
              {currentQuestionId ? (
                <VoiceShellRoot>
                  <CopilotAppProvider threadId={copilotThreadId}>
                    {detailReady ? (
                      <SessionReviewTutorSection
                        sessionId={sessionId}
                        tutorView={tutorView}
                        detail={detail}
                        analyzing={analyzing}
                        onAnalyze={handleAnalyze}
                      />
                    ) : (
                      <div
                        className="flex min-h-[12rem] items-center justify-center rounded-lg bg-muted/20"
                        aria-busy="true"
                      >
                        <p className="text-sm text-muted-foreground">加载讲解内容…</p>
                      </div>
                    )}
                  </CopilotAppProvider>
                </VoiceShellRoot>
              ) : (
                <div className="flex min-h-[12rem] items-center justify-center rounded-lg bg-muted/20">
                  <p className="text-sm text-muted-foreground">请选择题目</p>
                </div>
              )}
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}
