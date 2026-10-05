const URL_PATTERN =
  /https?:\/\/[^\s<>()]+|(?<![a-z0-9@.-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}(?:\/[^\s<>()]*)?/g;

export function descriptionParts(text) {
  const result = [];
  let last = 0;
  for (const match of text.matchAll(URL_PATTERN)) {
    if (match.index > last) {
      result.push({ type: "text", value: text.slice(last, match.index) });
    }
    const label = match[0].replace(/[.,]+$/, "");
    const href = /^https?:\/\//.test(label) ? label : `https://${label}`;
    result.push({ type: "link", href, label });
    last = match.index + label.length;
  }
  if (last < text.length || result.length === 0) {
    result.push({ type: "text", value: text.slice(last) });
  }
  return result;
}
