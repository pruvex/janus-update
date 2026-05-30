function threadTimestampMs(thread) {
  const internalRaw = Number(thread?.internal_date_ms || 0);
  if (Number.isFinite(internalRaw) && internalRaw > 0) return internalRaw;
  const parsed = Date.parse(String(thread?.date || ""));
  if (Number.isFinite(parsed) && parsed > 0) return parsed;
  return 0;
}

function sortThreadsChronologically(threads) {
  const list = Array.isArray(threads) ? [...threads] : [];
  list.sort((a, b) => threadTimestampMs(b) - threadTimestampMs(a));
  return list;
}

export function filterMailThreads(threads, query) {
  const list = sortThreadsChronologically(threads);
  const q = String(query || "")
    .trim()
    .toLowerCase();
  if (!q) return list;
  return list.filter((thread) => {
    const subject = String(thread?.subject || "").toLowerCase();
    const from = String(thread?.from_display || thread?.from || "").toLowerCase();
    const snippet = String(thread?.snippet || "").toLowerCase();
    return subject.includes(q) || from.includes(q) || snippet.includes(q);
  });
}
