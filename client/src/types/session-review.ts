export type QuestionType =
  | 'fill_blank'
  | 'multiple_choice'
  | 'calculation'
  | 'word_problem'
  | 'unknown'

export interface ChoiceOption {
  key: string
  text: string
}

export type Verdict = 'correct' | 'wrong' | 'unknown'

export type AnalysisStatus = 'missing' | 'pending' | 'generating' | 'ready' | 'failed'

export type ErrorCategory =
  | 'correct'
  | 'concept_error'
  | 'calculation_error'
  | 'incomplete'
  | 'unknown'

export interface ErrorClassification {
  category: ErrorCategory
  subcategory?: string
  confidence?: number
}

export interface TimelineSegment {
  question_id: string
  number: number
  start_ms: number
  end_ms: number
  verdict: Verdict
}

export interface SessionTimelineIndex {
  schema_version: string
  session_id: string
  duration_ms: number
  segments: TimelineSegment[]
}

export interface QuestionSummary {
  question_id: string
  number: number
  question_type?: QuestionType
  verdict: Verdict
  active_duration_ms: number
  prompt_preview: string
  answer_preview: string
  summary: string
  analysis_status: AnalysisStatus
  stale: boolean
}

export interface TutorAnalysisPolicy {
  data_source: 'mock' | 'live'
  manual_only: boolean
  prefetch_on_select: boolean
  auto_analyze_on_view: boolean
}

export interface TutorViewResponse {
  timeline_index: SessionTimelineIndex
  questions: QuestionSummary[]
  analysis_policy: TutorAnalysisPolicy
}

export interface TimelineEntry {
  t_offset_ms: number
  kind: 'appeared' | 'changed' | 'erased'
  text: string
  prev_text?: string
  frame_id?: string
  confidence?: number
}

export interface FocusSegment {
  segment_index?: number
  start_ms: number
  end_ms: number
  duration_ms: number
}

export interface QuestionProcessPackage {
  schema_version: string
  session_id: string
  question_id: string
  number: number
  question_type?: QuestionType
  status?: 'building' | 'complete' | 'updating'
  prompt: { text: string; options?: ChoiceOption[] }
  final_answer: { text: string; confidence?: number }
  answer_timeline: TimelineEntry[]
  focus_segments: FocusSegment[]
  process_metrics: {
    active_duration_ms: number
    revision_count: number
    stuck?: boolean
    idle_periods_ms?: Array<{
      start_ms: number
      end_ms: number
      duration_ms: number
    }>
  }
  scratch_work?: Array<{ text: string; region_id?: string; confidence?: number }>
}

export interface TutorContent {
  schema_version: string
  question_id: string
  analysis_status: AnalysisStatus
  verdict: Verdict
  reference_answer: string
  summary: string
  explanation_paragraphs: string[]
  error_classification?: ErrorClassification
  process_comment?: string
  actions?: Array<{ id: string; label: string; enabled: boolean }>
  stale?: boolean
  generated_at?: string
  model?: string
  error?: string | null
}

export interface QuestionDetailResponse {
  package: QuestionProcessPackage
  tutor: TutorContent
}
