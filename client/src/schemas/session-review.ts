import { z } from 'zod'

const verdictSchema = z.enum(['correct', 'wrong', 'unknown'])
const analysisStatusSchema = z.enum(['missing', 'pending', 'generating', 'ready', 'failed'])
const questionTypeSchema = z.enum([
  'fill_blank',
  'multiple_choice',
  'calculation',
  'word_problem',
  'unknown',
])
const errorCategorySchema = z.enum([
  'correct',
  'concept_error',
  'calculation_error',
  'incomplete',
  'unknown',
])

const timelineSegmentSchema = z.object({
  question_id: z.string(),
  number: z.number(),
  start_ms: z.number(),
  end_ms: z.number(),
  verdict: verdictSchema,
})

const sessionTimelineIndexSchema = z
  .object({
    schema_version: z.string(),
    session_id: z.string(),
    duration_ms: z.number(),
    segments: z.array(timelineSegmentSchema),
  })
  .passthrough()

const questionSummarySchema = z.object({
  question_id: z.string(),
  number: z.number(),
  verdict: verdictSchema,
  active_duration_ms: z.number(),
  prompt_preview: z.string(),
  answer_preview: z.string(),
  summary: z.string(),
  analysis_status: analysisStatusSchema,
  stale: z.boolean(),
  question_type: questionTypeSchema.optional(),
})

const tutorAnalysisPolicySchema = z.object({
  data_source: z.enum(['mock', 'live']),
  manual_only: z.boolean(),
  prefetch_on_select: z.boolean(),
  auto_analyze_on_view: z.boolean(),
})

export const tutorViewResponseSchema = z.object({
  timeline_index: sessionTimelineIndexSchema,
  questions: z.array(questionSummarySchema),
  analysis_policy: tutorAnalysisPolicySchema,
})

const errorClassificationSchema = z
  .object({
    category: errorCategorySchema,
    subcategory: z.string().nullish(),
    confidence: z.number().nullish(),
  })
  .passthrough()

const tutorContentSchema = z
  .object({
    schema_version: z.string(),
    question_id: z.string(),
    analysis_status: analysisStatusSchema,
    verdict: verdictSchema,
    reference_answer: z.string(),
    summary: z.string(),
    explanation_paragraphs: z.array(z.string()),
    error_classification: errorClassificationSchema.optional(),
    process_comment: z.string().nullish(),
    actions: z
      .array(
        z.object({
          id: z.string(),
          label: z.string(),
          enabled: z.boolean(),
        }),
      )
      .optional(),
    stale: z.boolean().optional(),
    generated_at: z.string().optional(),
    model: z.string().optional(),
    error: z.string().nullable().optional(),
  })
  .passthrough()

const questionProcessPackageSchema = z
  .object({
    schema_version: z.string(),
    session_id: z.string(),
    question_id: z.string(),
    prompt: z.record(z.string(), z.unknown()),
    final_answer: z.record(z.string(), z.unknown()),
    answer_timeline: z.array(z.record(z.string(), z.unknown())).optional(),
    focus_segments: z.array(z.record(z.string(), z.unknown())).optional(),
    process_metrics: z.record(z.string(), z.unknown()),
  })
  .passthrough()

export const questionDetailResponseSchema = z.object({
  package: questionProcessPackageSchema,
  tutor: tutorContentSchema,
})

export const analyzeQuestionResponseSchema = z.object({
  analysis_status: z.string(),
})

export type TutorViewResponseParsed = z.infer<typeof tutorViewResponseSchema>
export type QuestionDetailResponseParsed = z.infer<typeof questionDetailResponseSchema>

export function parseTutorViewResponse(data: unknown): TutorViewResponseParsed {
  return tutorViewResponseSchema.parse(data)
}

export function parseQuestionDetailResponse(data: unknown): QuestionDetailResponseParsed {
  return questionDetailResponseSchema.parse(data)
}

export function parseSseTutorContent(data: unknown): z.infer<typeof tutorContentSchema> {
  return tutorContentSchema.parse(data)
}
