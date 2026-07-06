export interface TutorSessionContext {
  schema_version: 'home-tutor.tutor-session-context.v1'
  page: 'session_review'
  session_id: string
  question_id: string
  navigation: {
    question_index: number
    total_questions: number
    timeline_ms?: number
  }
  package: {
    prompt_text: string
    options?: Array<{ key: string; text: string }>
    final_answer: string
    question_type?: string
    verdict: 'correct' | 'wrong' | 'unknown'
    process_summary?: string
  }
  tutor: {
    summary: string
    error_category?: string
    explanation_paragraphs: string[]
    analysis_status: string
  }
  a2ui: {
    surface_id: string
    data_model: Record<string, unknown>
    recent_actions: Array<{ id: string; ts: number }>
  }
  transcript: Array<{
    role: 'user' | 'assistant'
    content: string
    source: 'asr' | 'text' | 'action'
    ts: number
  }>
  vision_hints?: Array<{
    region_id: string
    reason: string
    layout_hash: string
  }>
}

export type TranscriptEntry = TutorSessionContext['transcript'][number]
