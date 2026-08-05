/** Strip leading emoji / symbols so legend relies on color markers. */
export function stripLeadingEmoji(label: string): string {
  return label
    .replace(/^[\p{Extended_Pictographic}\p{Emoji_Presentation}\uFE0F\u200D\s]+/u, '')
    .trim()
}
