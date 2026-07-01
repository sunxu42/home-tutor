import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

interface ReviewSectionProps {
  title: string
  children: ReactNode
  className?: string
}

/** 扁平区块：仅用分隔线与间距，不用卡片 */
export function ReviewSection({ title, children, className }: ReviewSectionProps) {
  return (
    <section className={cn('border-b border-border/50 py-3 last:border-b-0', className)}>
      <h3 className="mb-2 text-xs font-medium text-muted-foreground">{title}</h3>
      {children}
    </section>
  )
}
