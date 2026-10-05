export function themeView({ saved, telegramScheme } = {}) {
  const followed = telegramScheme === "dark" ? "dark" : "light";
  const choice = saved === "light" || saved === "dark" ? saved : followed;
  return {
    choice,
    label: choice === "dark" ? "Светлая тема" : "Тёмная тема",
    knob: choice,
  };
}
