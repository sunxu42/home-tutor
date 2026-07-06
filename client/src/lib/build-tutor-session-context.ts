import type { QuestionDetailResponse, TutorViewResponse } from '@/types/session-review'
import type { TutorSessionContext } from '@/types/tutor-session-context'

export function buildTutorSessionContext(args: {
  sessionId: string
  detail: QuestionDetailResponse
  tutorView: TutorViewResponse
  a2uiDataModel: Record<string, unknown>
  recentActions: Array<{ id: string; ts: number }>
  transcript: TutorSessionContext['transcript']
}): TutorSessionContext {
  const { package: pkg, tutor } = args.detail
  const idx = args.tutorView.questions.findIndex((q) => q.question_id === pkg.question_id)
  const metrics = pkg.process_metrics

  return {
    schema_version: 'home-tutor.tutor-session-context.v1',
    page: 'session_review',
    session_id: args.sessionId,
    question_id: pkg.question_id,
    navigation: {
      question_index: idx >= 0 ? idx + 1 : 1,
      total_questions: args.tutorView.questions.length,
    },
    package: {
      prompt_text: pkg.prompt.text,
      options: pkg.prompt.options,
      final_answer: pkg.final_answer.text,
      question_type: pkg.question_type,
      verdict: tutor.verdict,
      process_summary: `用时约${Math.floor(metrics.active_duration_ms / 1000)}秒，修改${metrics.revision_count}次`,
    },
    tutor: {
      summary: tutor.summary,
      error_category: tutor.error_classification?.category,
      explanation_paragraphs: tutor.explanation_paragraphs,
      analysis_status: tutor.analysis_status,
    },
    a2ui: {
      surface_id: 'tutor-panel',
      data_model: args.a2uiDataModel,
      recent_actions: args.recentActions,
    },
    transcript: args.transcript,
  }
}
