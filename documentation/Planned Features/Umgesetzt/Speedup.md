Ein "Turbo-Flow" Epic würde folgende Punkte angehen:
Parallel Execution (Memory vs. Tools):
Aktuell läuft vieles hintereinander. Wir könnten die Vektorsuche und den Fact-Coupon-Matcher parallel zum ersten "Thinking-Call" des Modells starten.
Streaming-Optimierung:
Wir minimieren die "Time-to-First-Token". Wir optimieren den SSE-Stream (Server-Sent Events), damit die Antwort sofort losrattert, während im Hintergrund noch die Metadaten (Kosten, Usage) berechnet werden.
Caching 2.0 (Model-States):
Wir nutzen aggressiveres Caching für die Tool-Definitionen und System-Prompts, damit das LLM bei jeder Nachricht weniger "Vorgeplänkel" verarbeiten muss.
Async Extraction:
Wir lagern die Memory-Extraktion (die nach der Antwort passiert) komplett in einen entkoppelten Hintergrund-Prozess aus, damit der User sofort wieder tippen kann, ohne dass das System "beschäftigt" wirkt.
Das Ziel von Turbo-Flow:
Janus soll sich "instant" anfühlen. Eine Latenz-Reduktion von ~30-50% über das gesamte System hinweg.