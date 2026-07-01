import { ChoiceOptionsList } from '@/components/session-review/ChoiceOptionsList'
import { QuestionProcessMiniBar } from '@/components/session-review/QuestionProcessMiniBar'
import { QuestionTypeBadge } from '@/components/session-review/QuestionTypeBadge'
import { ReviewSection } from '@/components/session-review/ReviewSection'
import { ScratchWorkSection } from '@/components/session-review/ScratchWorkSection'
import type { QuestionProcessPackage, TutorContent } from '@/types/session-review'

interface QuestionContextPanelProps {
  package: QuestionProcessPackage
  tutor: TutorContent
}

export function QuestionContextPanel({ package: pkg, tutor }: QuestionContextPanelProps) {
  const questionType = pkg.question_type ?? 'unknown'
  const options = pkg.prompt.options ?? []
  const optionsShowAnswer = questionType === 'multiple_choice' && options.length > 0
  const showAnswerSection = !optionsShowAnswer
  const showReference =
    showAnswerSection && tutor.verdict === 'wrong' && tutor.reference_answer

  return (
    <div className="space-y-0">
      <ReviewSection title={`第 ${pkg.number} 题`}>
        <QuestionTypeBadge type={questionType} />
        <p className="mt-2 text-base leading-relaxed">{pkg.prompt.text}</p>
      </ReviewSection>

      {optionsShowAnswer ? (
        <ReviewSection title="选项">
          <ChoiceOptionsList
            options={options}
            studentAnswer={pkg.final_answer.text}
            referenceAnswer={tutor.reference_answer}
          />
        </ReviewSection>
      ) : null}

      {showAnswerSection ? (
        <ReviewSection title="你的答案">
          <p className="text-base font-semibold">{pkg.final_answer.text || '（未识别）'}</p>
          {showReference ? (
            <p className="mt-1 text-sm text-muted-foreground">
              参考：{tutor.reference_answer}
            </p>
          ) : null}
        </ReviewSection>
      ) : null}

      <QuestionProcessMiniBar package={pkg} />
      <ScratchWorkSection items={pkg.scratch_work ?? []} />
    </div>
  )
}
