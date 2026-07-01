import { useMemo } from 'react'
import { Link } from 'react-router-dom'

import { type Session, type Subject } from '@/services/api'

interface SessionCardProps {
  session: Session
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}/${m}/${day}`
}

function accuracyTone(accuracy: number): string {
  if (accuracy >= 85) return 'text-[#4A7C6F]'
  if (accuracy >= 60) return 'text-[#A8814A]'
  return 'text-[#A65A4A]'
}

export function SessionCard({ session }: SessionCardProps) {
  return (
    <Link
      to={`/sessions/${session.id}/review`}
      className="group block rounded-lg border border-border bg-card p-5 transition-all duration-200 hover:border-[#4A7C6F]/40 hover:shadow-[0_2px_8px_rgba(45,42,38,0.08)]"
    >
      <div className="flex items-baseline justify-between gap-4">
        <div className="flex items-baseline gap-3">
          <span className="text-base font-medium text-foreground font-serif tracking-wide">
            {session.subject}
          </span>
          <span className={`text-sm font-mono ${accuracyTone(session.accuracy)}`}>
            {session.accuracy.toFixed(1)}% 正确率
          </span>
        </div>
        <span className="text-xs text-muted-foreground tabular-nums">
          {formatDate(session.session_time)}
        </span>
      </div>
      <div className="mt-2 h-px w-12 bg-border transition-all duration-300 group-hover:w-20 group-hover:bg-[#4A7C6F]/40" />
    </Link>
  )
}

interface SubjectFilterProps {
  subjects: Subject[]
  selected: Subject | null
  onChange: (subject: Subject | null) => void
}

export function SubjectFilter({ subjects, selected, onChange }: SubjectFilterProps) {
  return (
    <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
      <FilterChip active={selected === null} onClick={() => onChange(null)}>
        全部
      </FilterChip>
      {subjects.map((s) => (
        <FilterChip key={s} active={selected === s} onClick={() => onChange(s)}>
          {s}
        </FilterChip>
      ))}
    </div>
  )
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        'shrink-0 rounded-md px-4 py-1.5 text-sm transition-colors duration-150 ' +
        (active
          ? 'bg-[#4A7C6F] text-[#FAF7F2] shadow-sm'
          : 'bg-[#F0EBE3] text-[#5C5651] hover:bg-[#E8E2D9]')
      }
    >
      {children}
    </button>
  )
}

interface HomePageProps {
  sessions: Session[]
  subjects: Subject[]
  selectedSubject: Subject | null
  onSelectSubject: (subject: Subject | null) => void
  loading: boolean
  error: string | null
}

export function HomePage({
  sessions,
  subjects,
  selectedSubject,
  onSelectSubject,
  loading,
  error,
}: HomePageProps) {
  const title = useMemo(() => {
    if (loading) return '正在检视书架…'
    if (error) return '连接中断'
    if (sessions.length === 0) return '书架尚空'
    return '卷帙 · 作业回顾'
  }, [loading, error, sessions.length])

  const subtitle = useMemo(() => {
    if (loading) return '正在从后端取回记录…'
    if (error) return error
    if (sessions.length === 0) return '还没有任何会话记录。'
    return `共 ${sessions.length} 篇${selectedSubject ? `· ${selectedSubject}` : ''}`
  }, [loading, error, sessions.length, selectedSubject])

  return (
    <div className="mx-auto flex min-h-svh max-w-5xl flex-col gap-8 px-4 py-10 sm:px-6 lg:px-8">
      <header className="space-y-3 border-b border-border/60 pb-8">
        <div className="flex items-baseline justify-between">
          <h1 className="text-3xl font-semibold tracking-wide text-foreground sm:text-4xl">
            <span className="font-serif">Home Tutor</span>
          </h1>
          <span className="hidden text-xs tracking-[0.3em] text-muted-foreground sm:inline">
            卷 · 帙
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-xs text-muted-foreground/80">{subtitle}</p>
      </header>

      <section aria-label="科目筛选" className="space-y-3">
        <h2 className="text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          分类
        </h2>
        <SubjectFilter
          subjects={subjects}
          selected={selectedSubject}
          onChange={onSelectSubject}
        />
      </section>

      <section aria-label="会话列表" className="flex-1">
        {loading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-20 animate-pulse rounded-lg border border-border/50 bg-card/60"
              />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {sessions.map((s) => (
              <SessionCard key={s.id} session={s} />
            ))}
          </div>
        )}
      </section>

      <footer className="border-t border-border/60 pt-6 text-center text-xs tracking-wider text-muted-foreground">
        <span className="font-serif">— 循序而进，温故知新 —</span>
      </footer>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border/70 bg-card/40 px-6 py-16 text-center">
      <p className="font-serif text-base text-muted-foreground">书架尚空</p>
      <p className="mt-2 text-xs text-muted-foreground/70">
        重启服务端后会自动导入 fixture 会话；也可通过 API 手动创建。
      </p>
      <code className="mt-4 inline-block rounded bg-muted px-2 py-1 font-mono text-xs text-muted-foreground">
        POST /api/sessions
      </code>
    </div>
  )
}
