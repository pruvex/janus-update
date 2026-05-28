export function mapMailStatusToUi(statusPayload) {
  const status = String(statusPayload?.status || "").trim();
  const accountHint = statusPayload?.account_hint ? String(statusPayload.account_hint) : "";
  const errorMessage = statusPayload?.error_message ? String(statusPayload.error_message) : "";

  if (status === "connected") {
    return {
      badge: "Verbunden",
      message: accountHint ? `Gmail ist verbunden (${accountHint}).` : "Gmail ist verbunden.",
    };
  }
  if (status === "missing_scope") {
    return {
      badge: "Scope fehlt",
      message: "Gmail ist verbunden, aber Mail-Berechtigungen fehlen. Bitte Gmail neu autorisieren.",
    };
  }
  if (status === "sync_error") {
    return {
      badge: "Sync-Fehler",
      message: errorMessage || "Beim Abrufen des Mail-Status ist ein Fehler aufgetreten.",
    };
  }
  return {
    badge: "Getrennt",
    message: "Kein Gmail-Konto verbunden. Bitte Gmail verbinden.",
  };
}
