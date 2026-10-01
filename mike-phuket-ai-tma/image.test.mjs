import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("the mini app image copies every module the page imports", () => {
  const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
  const dockerfile = readFileSync(new URL("./Dockerfile", import.meta.url), "utf8");
  const copied = dockerfile
    .split("\n")
    .filter((line) => line.trim().startsWith("COPY "))
    .join(" ");
  const imports = [...html.matchAll(/from "\.\/([^"]+\.mjs)"/g)].map((match) => match[1]);

  assert.ok(imports.includes("chat.mjs"));
  for (const name of imports) {
    assert.ok(copied.includes(name), `${name} is imported by the page but not copied into the image`);
  }
});
