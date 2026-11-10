import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

function importedModules(source) {
  return [...source.matchAll(/from "\.\/([^"]+\.mjs)"/g)].map((match) => match[1]);
}

test("the mini app image ships every module the page imports", () => {
  const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
  const dockerfile = readFileSync(new URL("./Dockerfile", import.meta.url), "utf8");
  const copied = dockerfile
    .split("\n")
    .filter((line) => line.startsWith("COPY ") && line.includes(".mjs"))
    .join(" ");
  const needed = new Set(importedModules(html));
  for (const file of [...needed]) {
    const source = readFileSync(new URL(`./${file}`, import.meta.url), "utf8");
    for (const nested of importedModules(source)) needed.add(nested);
  }
  for (const file of needed) {
    assert.match(copied, new RegExp(`\\b${file}\\b`));
  }
});
