const SOURCE_LABELS: Record<string, string> = {
  unknown: 'Неизвестно',
  instagram: 'Instagram',
  facebook: 'Facebook',
}

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source.charAt(0).toUpperCase() + source.slice(1)
}
