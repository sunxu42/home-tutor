import { Button } from '@/components/ui/button'

import type { CatalogRenderers } from '@copilotkit/a2ui-renderer'

import { homeTutorDefinitions } from './definitions'

export const homeTutorRenderers: CatalogRenderers<typeof homeTutorDefinitions> = {
  TutorText: ({ props }) => (
    <p className="text-sm leading-relaxed text-foreground/90">{props.text}</p>
  ),
  ActionChip: ({ props, dispatch }) => (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className="h-7 rounded-md bg-muted/60 text-xs"
      onClick={() => dispatch?.({ name: props.actionId })}
    >
      {props.label}
    </Button>
  ),
  AnswerCompare: ({ props }) => (
    <div className="grid grid-cols-2 gap-2 rounded-lg border border-border/60 bg-muted/30 p-3 text-sm">
      <div>
        <p className="text-xs text-muted-foreground">你的答案</p>
        <p className="font-medium">{props.student || '—'}</p>
      </div>
      <div className="rounded-md bg-background/80 p-2">
        <p className="text-xs text-muted-foreground">参考答案</p>
        <p className="font-medium text-primary">{props.reference || '—'}</p>
      </div>
    </div>
  ),
  ProcessStep: ({ props }) => (
    <div className="rounded-lg border border-border/50 bg-background p-3">
      <p className="text-xs font-medium text-muted-foreground">{props.title ?? '步骤'}</p>
      <p className="mt-1 text-sm leading-relaxed">{props.text}</p>
    </div>
  ),
  HintLadder: ({ props }) => {
    if (!props.items.length) {
      return null
    }
    return (
      <ol className="space-y-1.5 rounded-lg bg-amber-50/80 p-3 text-sm dark:bg-amber-950/20">
        {props.items.map((item, index) => (
          <li key={`${index}-${item}`} className="flex gap-2">
            <span className="font-medium text-amber-700 dark:text-amber-300">{index + 1}.</span>
            <span>{item}</span>
          </li>
        ))}
      </ol>
    )
  },
  KeyFrameThumb: ({ props }) => (
    <div className="overflow-hidden rounded-lg border border-border/60 bg-muted/20">
      <p className="border-b border-border/50 px-2 py-1 text-xs text-muted-foreground">
        {props.label ?? '关键帧'}
        {props.frameId ? ` · ${props.frameId}` : ''}
      </p>
      {props.imageUrl ? (
        <img
          src={props.imageUrl}
          alt={props.label ?? '关键帧'}
          className="max-h-32 w-full object-cover"
        />
      ) : (
        <div className="flex h-20 items-center justify-center text-xs text-muted-foreground">
          暂无图片
        </div>
      )}
    </div>
  ),
}
