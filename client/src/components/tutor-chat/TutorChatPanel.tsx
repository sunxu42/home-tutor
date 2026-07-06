import { type FormEvent, useState } from 'react'
import { Loader2, Send } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface TutorChatPanelProps {
  disabled?: boolean
  loading?: boolean
  onSend: (message: string) => void
}

export function TutorChatPanel({ disabled = false, loading = false, onSend }: TutorChatPanelProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || disabled || loading) {
      return
    }
    onSend(trimmed)
    setInput('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 flex items-center gap-2 border-t border-border/50 pt-3"
    >
      <input
        type="text"
        value={input}
        onChange={(event) => setInput(event.target.value)}
        placeholder="问问老师…"
        disabled={disabled || loading}
        className="flex-1 rounded-lg border border-border/60 bg-background px-3 py-2 text-sm outline-none focus:border-primary"
      />
      <Button type="submit" size="sm" disabled={disabled || loading || !input.trim()}>
        {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Send className="h-4 w-4" aria-hidden />}
        <span className="sr-only">发送</span>
      </Button>
    </form>
  )
}
