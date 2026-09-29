(() => {
  const thread = document.getElementById("thread");
  const form = document.getElementById("composer");
  const field = document.getElementById("message");
  const send = form.querySelector('button[type="submit"]');
  const portraitSrc = "./assets/mike-portrait.jpg";
  const portraitSrcSet =
    "./assets/mike-portrait.jpg 328w, ./assets/mike-portrait@2x.jpg 656w";

  const replies = [
    "Ок. Важнее море, еда или вид сверху?",
    "Ты на байке или без?",
    "До которого часа свободен? Подберу короткий маршрут.",
  ];
  let replyAt = 0;
  let busy = false;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function face() {
    const wrap = document.createElement("div");
    wrap.className = "chat-face";
    const img = document.createElement("img");
    img.src = portraitSrc;
    img.srcset = portraitSrcSet;
    img.sizes = "32px";
    img.alt = "";
    img.width = 32;
    img.height = 32;
    wrap.append(img);
    return wrap;
  }

  function appendUser(text) {
    const row = document.createElement("div");
    row.className = "row row--user";
    const bubble = document.createElement("p");
    bubble.className = "bubble bubble--user";
    bubble.textContent = text;
    row.append(bubble);
    thread.append(row);
  }

  function appendMike(text) {
    const row = document.createElement("div");
    row.className = "row row--mike";
    const bubble = document.createElement("p");
    bubble.className = "bubble bubble--mike";
    bubble.textContent = text;
    row.append(face(), bubble);
    thread.append(row);
  }

  function appendTyping() {
    const row = document.createElement("div");
    row.className = "row row--mike";
    row.dataset.typing = "true";
    const bubble = document.createElement("div");
    bubble.className = "bubble bubble--mike";
    bubble.setAttribute("aria-label", "Майк печатает");
    const dots = document.createElement("div");
    dots.className = "typing";
    dots.innerHTML = "<span></span><span></span><span></span>";
    bubble.append(dots);
    row.append(face(), bubble);
    thread.append(row);
    return row;
  }

  function scrollToEnd() {
    thread.scrollTop = thread.scrollHeight;
  }

  function resizeField() {
    field.style.height = "auto";
    field.style.height = `${Math.min(field.scrollHeight, 120)}px`;
  }

  function setBusy(next) {
    busy = next;
    field.disabled = next;
    send.disabled = next || !field.value.trim();
  }

  field.addEventListener("input", () => {
    send.disabled = busy || !field.value.trim();
    resizeField();
  });

  field.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = field.value.trim();
    if (!text || busy) return;

    appendUser(text);
    field.value = "";
    field.style.height = "";
    setBusy(true);
    scrollToEnd();

    const typing = appendTyping();
    scrollToEnd();

    const wait = reduceMotion ? 0 : 520;
    window.setTimeout(() => {
      typing.remove();
      const reply = replies[Math.min(replyAt, replies.length - 1)];
      replyAt += 1;
      appendMike(reply);
      setBusy(false);
      field.focus();
      scrollToEnd();
    }, wait);
  });

  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#F4F7FB");
    tg.setBackgroundColor("#F4F7FB");
    tg.BackButton.show();
    tg.BackButton.onClick(() => {
      window.location.href = "./index.html";
    });
  }

  send.disabled = true;
  scrollToEnd();
})();
