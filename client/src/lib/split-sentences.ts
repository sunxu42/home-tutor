export function splitChineseSentences(text: string): string[] {
  const normalized = text.trim()
  if (!normalized) {
    return []
  }
  const parts = normalized
    .split(/(?<=[。！？!?；;])/u)
    .map((part) => part.trim())
    .filter(Boolean)
  return parts.length > 0 ? parts : [normalized]
}
