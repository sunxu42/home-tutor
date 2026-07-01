import { ReviewSection } from '@/components/session-review/ReviewSection'

interface ScratchWorkSectionProps {
  items: Array<{ text: string; region_id?: string }>
}

export function ScratchWorkSection({ items }: ScratchWorkSectionProps) {
  if (items.length === 0) {
    return null
  }

  return (
    <ReviewSection title="草稿">
      <ul className="space-y-1.5 text-sm">
        {items.map((item, index) => (
          <li key={`${item.region_id ?? 'scratch'}-${index}`} className="text-foreground/90">
            {item.text}
          </li>
        ))}
      </ul>
    </ReviewSection>
  )
}
