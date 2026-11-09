const GREETING = "Привет! Я Майк. Спрашивай что угодно о Пхукете.";
const URL_PATTERN = /https?:\/\/[^\s<>()]+/g;

function parts(content) {
  const result = [];
  let last = 0;
  for (const match of content.matchAll(URL_PATTERN)) {
    if (match.index > last) {
      result.push({ type: "text", value: content.slice(last, match.index) });
    }
    result.push({ type: "link", href: match[0] });
    last = match.index + match[0].length;
  }
  if (last < content.length || result.length === 0) {
    result.push({ type: "text", value: content.slice(last) });
  }
  return result;
}

export function waitingView() {
  return {
    role: "mike",
    dots: true,
    text: "Думаю как местный 😎",
  };
}

export function failureView() {
  return {
    role: "mike",
    parts: [{ type: "text", value: "Не получилось ответить. Напиши ещё раз." }],
  };
}

export function canSend({ signedIn, busy, text }) {
  return Boolean(signedIn) && !busy && text.trim().length > 0;
}

export function homeAsk({ signedIn, busy, text }) {
  const draft = text.trim();
  const send = canSend({ signedIn, busy, text: draft });
  return { openChat: true, send, draft: send ? "" : draft };
}

function tmaHeaders(initData) {
  return { Authorization: `tma ${initData}` };
}

export async function loadThread({ initData, fetch }) {
  const response = await fetch("/api/tma/messages", { headers: tmaHeaders(initData) });
  if (!response.ok) throw new Error("thread");
  const body = await response.json();
  return body.messages;
}

export async function postMessage({ text, initData, fetch }) {
  const response = await fetch("/api/tma/messages", {
    method: "POST",
    headers: { ...tmaHeaders(initData), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error("send");
  const body = await response.json();
  return body.reply;
}

export function threadView(messages) {
  const source = messages.length
    ? messages
    : [{ role: "assistant", content: GREETING }];
  return {
    bubbles: source.map((message) => ({
      role: message.role === "user" ? "user" : "mike",
      parts: parts(message.content),
    })),
  };
}
