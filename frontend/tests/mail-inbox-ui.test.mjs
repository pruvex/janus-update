import test from "node:test";
import assert from "node:assert/strict";

import { filterMailThreads } from "../js/mail-inbox-ui.js";

const THREADS = [
  { subject: "Build Report", from: "ci@example.com", snippet: "Pipeline gruen." },
  { subject: "Sprint Planung", from: "team@example.com", snippet: "Mail Modul Phase 2." },
];

test("filterMailThreads returns all entries for empty query", () => {
  const out = filterMailThreads(THREADS, "");
  assert.equal(out.length, 2);
});

test("filterMailThreads matches subject/from/snippet case-insensitive", () => {
  assert.equal(filterMailThreads(THREADS, "build").length, 1);
  assert.equal(filterMailThreads(THREADS, "TEAM@EXAMPLE.COM").length, 1);
  assert.equal(filterMailThreads(THREADS, "phase 2").length, 1);
});

test("filterMailThreads returns empty when nothing matches", () => {
  const out = filterMailThreads(THREADS, "invoice");
  assert.equal(out.length, 0);
});
