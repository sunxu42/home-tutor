import { describe, expect, it } from 'vitest'

import { buildTutorSessionContext } from '@/lib/build-tutor-session-context'
import {
  parseQuestionDetailResponse,
  parseTutorViewResponse,
} from '@/schemas/session-review'
import type { QuestionDetailResponse, TutorViewResponse } from '@/types/session-review'

const minimalTutorView: TutorViewResponse = {
  timeline_index: {
    schema_version: 'home-tutor.session-timeline-index.v1',
    session_id: 'sess-1',
    duration_ms: 60000,
    segments: [
      {
        question_id: 'q01',
        number: 1,
        start_ms: 0,
        end_ms: 60000,
        verdict: 'wrong',
      },
    ],
  },
  questions: [
    {
      question_id: 'q01',
      number: 1,
      verdict: 'wrong',
      active_duration_ms: 5000,
      prompt_preview: '1+1=?',
      answer_preview: '3',
      summary: '计算错误',
      analysis_status: 'ready',
      stale: false,
    },
  ],
  analysis_policy: {
    data_source: 'mock',
    manual_only: true,
    prefetch_on_select: false,
    auto_analyze_on_view: false,
  },
}

const minimalDetail: QuestionDetailResponse = {
  package: {
    schema_version: 'home-tutor.question-package.v1',
    session_id: 'sess-1',
    question_id: 'q01',
    number: 1,
    prompt: { text: '1+1=?' },
    final_answer: { text: '3' },
    answer_timeline: [],
    focus_segments: [],
    process_metrics: {
      active_duration_ms: 5000,
      revision_count: 1,
    },
  },
  tutor: {
    schema_version: 'home-tutor.tutor-content.v1',
    question_id: 'q01',
    analysis_status: 'ready',
    verdict: 'wrong',
    reference_answer: '2',
    summary: '计算错误',
    explanation_paragraphs: ['1+1 应该等于 2。'],
  },
}

describe('parseTutorViewResponse', () => {
  it('accepts a valid tutor view payload', () => {
    const parsed = parseTutorViewResponse(minimalTutorView)
    expect(parsed.questions).toHaveLength(1)
    expect(parsed.analysis_policy.data_source).toBe('mock')
  })

  it('rejects missing analysis_policy', () => {
    const { analysis_policy: _, ...invalid } = minimalTutorView
    expect(() => parseTutorViewResponse(invalid)).toThrow()
  })
})

describe('parseQuestionDetailResponse', () => {
  it('accepts a valid question detail payload', () => {
    const parsed = parseQuestionDetailResponse(minimalDetail)
    expect(parsed.package.question_id).toBe('q01')
    expect(parsed.tutor.verdict).toBe('wrong')
  })

  it('accepts null optional fields in error_classification', () => {
    const withNulls = {
      ...minimalDetail,
      tutor: {
        ...minimalDetail.tutor,
        error_classification: {
          category: 'calculation_error',
          subcategory: null,
          confidence: null,
        },
      },
    }
    const parsed = parseQuestionDetailResponse(withNulls)
    expect(parsed.tutor.error_classification?.category).toBe('calculation_error')
    expect(parsed.tutor.error_classification?.subcategory).toBeNull()
    expect(parsed.tutor.error_classification?.confidence).toBeNull()
  })
})

describe('buildTutorSessionContext', () => {
  it('builds navigation and package summary from detail', () => {
    const ctx = buildTutorSessionContext({
      sessionId: 'sess-1',
      detail: minimalDetail,
      tutorView: minimalTutorView,
      a2uiDataModel: {},
      recentActions: [],
      transcript: [],
    })

    expect(ctx.session_id).toBe('sess-1')
    expect(ctx.question_id).toBe('q01')
    expect(ctx.navigation.question_index).toBe(1)
    expect(ctx.navigation.total_questions).toBe(1)
    expect(ctx.package.prompt_text).toBe('1+1=?')
    expect(ctx.tutor.analysis_status).toBe('ready')
  })
})
