AUFTRAG: Erstellung des 'Janus Habitat Harvester' (Python)
ZIEL: Ein automatisiertes Skript zum Download von wissenschaftlich verifizierten Reptilien-Bildern für den Janus Diamond Standard.
1. TECHNISCHE PARAMETER
API: iNaturalist API V1 (https://api.inaturalist.org/v1/)
Zielpfad: C:\KI\Janus-Projekt\backend\tests\vision_matrix\Schlangen
Filter-Strenge:
Nur Beobachtungen mit quality_grade=research (Zertifizierte Forschungsklasse).
Nur Bilder mit freien Lizenzen (photo_license=cc-by,cc-by-nc,cc0).
Menge: Maximal 20 Bilder pro Spezies.
Qualität: Bevorzugt die URL-Endung original.jpg, Fallback auf large.jpg.
2. SPEZIES-LISTE (In das Skript integrieren)
Das Skript soll folgendes Array TARGET_SPECIES abarbeiten:
code
Python
TARGET_SPECIES = [
    # Clan der Boas
    "Boa constrictor", "Boa imperator", "Eunectes murinus", "Eunectes notaeus", 
    "Corallus caninus", "Corallus hortulana", "Epicrates cenchria", "Epicrates maurus", 
    "Candoia aspera", "Gongylophis colubrinus", "Chilabothrus inornatus", "Sanzinia madagascariensis",
    # Clan der Pythons
    "Python regius", "Python molurus", "Python bivittatus", "Malayopython reticulatus", 
    "Morelia viridis", "Morelia spilota", "Python sebae", "Antaresia childreni", 
    "Liasis olivaceus", "Python curtus", "Aspidites melanocephalus", "Morelia amethistina"
]
3. FUNKTIONS-LOGIK
Taxon-ID Suche: Das Skript muss zuerst für jeden Namen die taxon_id via /taxa Endpunkt ermitteln.
Ordner-Struktur: Erstelle für jede Spezies automatisch einen Unterordner im Zielpfad (z.B. .../Schlangen/Boa_constrictor/).
Download & Benennung:
Dateiname: [Wissenschaftlicher_Name]_[iNat_ID].jpg (Leerzeichen durch Unterstriche ersetzen).
Metadaten-Begleiter: Erstelle für JEDES Bild eine gleichnamige .json Datei im selben Ordner mit:
inaturalist_url, photographer_name, location (als String oder Koordinaten), observed_on (Datum).
Robustheit:
Implementiere time.sleep(1.5) zwischen den Downloads, um API-Sperren zu vermeiden.
Nutze requests für die API und den Download.
Error-Handling: Wenn eine Spezies keine Bilder liefert, überspringe sie mit einer Log-Meldung.
BITTE ERSTELLE DEN VOLLSTÄNDIGEN PYTHON-CODE JETZT.

---

## Vision Gate Status (Diamond, 2026-02-20)

- OpenWorld-Datensatz vorbereitet: `backend/tests/vision_matrix/OpenWorldStandard` (120 Bilder + 120 GT-JSONs).
- KPI-Doppel-Gates aktiv:
  - `npm run test:vision:stresstest:kpi`
  - `npm run test:vision:openworld`
- Erster token-effizienter Smoke-Run auf `001.jpg` wurde gestartet.
  - KPI grün (`contradiction_rate=0.000`, `source_map_coverage=1.000`)
  - STRICT-V3 aktuell noch rot (Detail-Mismatch auf `001.jpg`).

### Token-effizienter Testablauf

1. Nur ein Bild testen (`--image 001.jpg`).
2. Bei Fail nur dieses Bild nachschärfen und erneut testen.
3. Danach inkrementell mit `002.jpg`, `003.jpg`, ... fortfahren.
4. Full-Range/Full-Gate erst, wenn die Einzelbild-Smokes stabil grün sind.

Siehe Details in: `docs/VISION_TEST_STRATEGY_DIAMOND.md` und `docs/VISION_IMPLEMENTATION_LOG.md`.