# Skill Dossier: system.rss_news
**Status:** Diamond / Hybrid RSS-first
**Domain:** system

## Zweck
`system.rss_news` liefert schnelle aktuelle Nachrichtenlagen. Der Standardmodus `source="auto"` nutzt zuerst kuratierte RSS-Feeds, damit News-Anfragen ohne teure Websuche und mit hoher Quellenqualitaet beantwortet werden. Wenn RSS keine passenden Treffer liefert, darf die Provider-Websuche als Fallback genutzt werden.

## Feed-Set
Vorhandene Feeds: `spiegel`, `gamestar`, `tagesschau`, `zeit`, `heise`, `reuters`, `bbc`.

Ergaenzte Diamond-Feeds: `dlf`, `sz`, `handelsblatt`, `golem`, `ntv`.

`auto` priorisiert deutschsprachige Quellen: Tagesschau, Deutschlandfunk, SPIEGEL, ZEIT, Sueddeutsche Zeitung, Heise, Golem, Handelsblatt und n-tv. Reuters und BBC bleiben als gezielte Einzelquellen verfuegbar, werden aber nicht im deutschen Auto-Mix bevorzugt.

## Ausgabeformat
News-Antworten werden einheitlich gerendert:

```text
Kurzlage: ...

1. Meldungstitel (Datum)
2-3 Saetze Kurzbeschreibung.
Quelle: Quelle. Link

Einordnung:
...
```

Jeder Eintrag fuehrt die Quelle direkt am Eintrag. URLs werden als Markdown-Link hinter dem Wort `Link` versteckt.

## Routing
News-Intents wie `was gibt es neues`, `Nachrichten zu ...`, `aktuelle Meldungen` oder `Schlagzeilen` priorisieren `system.rss_news` vor `system.websearch`. Websearch bleibt Fallback, nicht Standardpfad.

## Link-Qualitaet
News-Websearch-Fallbacks nutzen eine zentrale Link-Quality-Schicht (`backend/services/websearch/link_quality.py`). Diese bewertet Quellen lokal und kostenneutral nach Intent, Sprache, Detailtiefe, Domain-Vertrauen und Ausschlussregeln.

Fuer News werden Detailartikel bevorzugt. Generische News-Uebersichten, Social-/Video-Seiten, Paywall-Quellen, Google-Suchseiten, SVG/XML-Namespace-URLs sowie OpenAI-Dokumentations-/Help-Center-Seiten werden fuer News nicht als Quellenlink verwendet. Dokumentationslinks bleiben fuer explizite API-/Docs-Intents erlaubt.

Wenn kein akzeptabler Detail-Link vorhanden ist, rendert Janus ehrlich `Link online leider nicht verfuegbar`, statt einen schlechten oder irrefuehrenden Link zu zeigen.
