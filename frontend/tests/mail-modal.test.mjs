import test from "node:test";
import assert from "node:assert/strict";

import { mapMailStatusToUi } from "../js/mail-status-ui.js";

test("mapMailStatusToUi maps connected status with account hint", () => {
  const ui = mapMailStatusToUi({
    status: "connected",
    account_hint: "user@example.com",
  });
  assert.equal(ui.badge, "Verbunden");
  assert.equal(ui.message, "Gmail ist verbunden (user@example.com).");
});

test("mapMailStatusToUi maps missing scope", () => {
  const ui = mapMailStatusToUi({
    status: "missing_scope",
  });
  assert.equal(ui.badge, "Scope fehlt");
  assert.match(ui.message, /Berechtigungen fehlen/);
});

test("mapMailStatusToUi maps sync error with backend message", () => {
  const ui = mapMailStatusToUi({
    status: "sync_error",
    error_message: "Token refresh failed",
  });
  assert.equal(ui.badge, "Sync-Fehler");
  assert.equal(ui.message, "Token refresh failed");
});

test("mapMailStatusToUi falls back to disconnected", () => {
  const ui = mapMailStatusToUi({
    status: "disconnected",
  });
  assert.equal(ui.badge, "Getrennt");
  assert.match(ui.message, /Kein Gmail-Konto verbunden/);
});
