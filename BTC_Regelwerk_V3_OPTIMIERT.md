# BTC 3x Hebel Trading Regelwerk – V3 OPTIMIERT

> **Legende:**
> - 🔴 **SCHWACHSTELLE** = Kritischer Fehler / Lücke im Original
> - 🟡 **VERBESSERUNG** = Optimierungsvorschlag
> - 🟢 **ORIGINAL OK** = Unverändert übernommen, funktioniert
> - ➕ **NEU** = Komplett neue Regel, im Original fehlend

---

## Bewertung des Originals (Zusammenfassung)

| Kategorie | Note | Kommentar |
|---|---|---|
| Grundstruktur | ⭐⭐⭐⭐ | Solide Basis, logischer Flow |
| Risikomanagement | ⭐⭐⭐ | Vorhanden, aber Lücken (kein Daily-Cap, kein Drawdown-Breaker) |
| Setups | ⭐⭐ | **Nur Short definiert – Long fehlt komplett** |
| Definitionen | ⭐⭐ | Zu vage ("flach", "Platz", "Struktur trailen") |
| Vollständigkeit | ⭐⭐ | Fehlende Elemente: Funding, Zeitfilter, Max-Positionen, Entry-Typ |
| Praxistauglichkeit | ⭐⭐⭐ | Nutzbar, aber Interpretationsspielraum führt zu Disziplinverlust |

**Gesamturteil: 6/10 – Guter Kern, aber nicht produktionsreif.** Die größten Probleme: fehlende Long-Setups, vage Definitionen und kein Drawdown-Schutz.

---

## 1. Ziel

🟢 **ORIGINAL OK**

Kapital schützen, Verluste klein halten, Gewinner laufen lassen.

---

## 2. Risiko & Positionsgröße

### 🟢 Basisregel (OK)
- **Risiko pro Trade = 0,5% vom Konto**

### 🔴 SCHWACHSTELLE: Positionsgrößen-Formel unklar

**Original:** `Positionsgröße = MIN(Risiko / Stop%, Kontogröße × 3)`

**Problem:** Die Formel vermischt zwei Dinge:
- `Risiko / Stop%` berechnet die nominelle Position für ein Risikolimit
- `Kontogröße × 3` ist einfach der maximale Hebel
- Bei 3x Hebel wirkt ein 0,5% Stop-Loss als **1,5% Kontoverlust** – das ist NICHT 0,5% Risiko

### 🟡 OPTIMIERT: Klare Formel mit Hebel-Berücksichtigung

```
Stop-Distanz     = Abstand Entry → Stop (in %)
Effektiver Loss  = Stop-Distanz × Hebel (3)
Max-Risiko       = 0,5% vom Konto

Positionsgröße (Basiswert) = (Kontogröße × Max-Risiko) / Stop-Distanz
Positionsgröße (gehebelt)  = Positionsgröße × Hebel

Begrenzung: Positionsgröße ≤ Kontogröße × 3 (max. Hebel)
```

**Beispiel:** Konto 10.000€, Stop 1,0% Distanz, 3x Hebel
- Risiko = 50€
- Position (Basis) = 50€ / 0,01 = 5.000€
- Position (gehebelt) = 5.000€ × 3 = 15.000€ → Cap bei 30.000€ → OK
- Effektiver Verlust = 1,0% × 3 = 3,0% von 5.000€ = 150€ → **zu viel!**
- Korrekt: Position = 50€ / (0,01 × 3) = 1.666€ Basis → 5.000€ gehebelt

### 🔴 SCHWACHSTELLE: "Kein Trade bei Stop < 0,4%"

**Problem:** Bei 3x Hebel ist 0,4% Stop = 1,2% Kontobewegung. Das ist für BTC oft zu eng → wird häufig ausgestoppt (Noise).

### 🟡 OPTIMIERT:
- **Minimum Stop-Distanz: 0,5%** (= 1,5% gehebelt, passend zu BTC-Volatilität)
- **Maximum Stop-Distanz: 2,0%** (= 6,0% gehebelt → zu riskant darüber)
- Dynamisch anpassen: ATR(14) auf 4H als Volatilitätsmaß. Stop ≥ 0,5× ATR(14).

### ➕ NEU: Maximale Positionsanzahl
- **Max. 2 gleichzeitige Positionen**
- Nie beide in gleicher Richtung (Klumpenrisiko)

---

## 3. Trendfilter (4H)

### 🟢 ORIGINAL OK (Grundidee)
- Über 200 EMA → Long
- Unter 200 EMA → Short

### 🔴 SCHWACHSTELLE: "EMA flach → kein Trade" – keine Definition

**Problem:** "Flach" ist subjektiv. Trader A sieht flach, Trader B sieht Trend → inkonsistente Entscheidungen.

### 🟡 OPTIMIERT: Messbare Flach-Definition
- **EMA-Steigung berechnen:** Δ = (EMA jetzt − EMA vor 10 Kerzen) / Preis × 100
- **Flach = |Δ| < 0,3%** über 10 Kerzen (4H = 40 Stunden)
- **Zusatz-Bestätigung:** Wenn ADX(14) auf 4H < 20 → Seitwärtsmarkt → kein Trade

### 🟡 VERBESSERUNG: Zweiter Trendfilter
- **Zusätzlich 50 EMA auf 4H** als Momentum-Check:
  - Long nur wenn Preis > 200 EMA **UND** 50 EMA > 200 EMA
  - Short nur wenn Preis < 200 EMA **UND** 50 EMA < 200 EMA
  - Divergenz (Preis über 200 aber 50 unter 200) → reduzierte Positionsgröße (50%)

---

## 4. Setup A – Pullback

### 🔴 SCHWACHSTELLE: Nur Short beschrieben – Long fehlt komplett

**Original nur Short:**
> Pullback zum 4H 20 EMA → 15m: Impuls → Pullback → Lower High → Break Tief

### 🟡 OPTIMIERT: Beide Richtungen + präzisere Regeln

#### Setup A – Short (Pullback in Abwärtstrend):
1. **4H:** Preis unter 200 EMA, 50 EMA unter 200 EMA
2. **4H:** Pullback zum 20 EMA (Preis berührt oder durchsticht 20 EMA)
3. **15m:** Impulskerze nach unten sichtbar
4. **15m:** Pullback bildet **Lower High** (unter dem 4H 20 EMA)
5. **15m:** Break unter das letzte Swing-Tief → **Entry**
6. **Stop:** Über dem Lower High + 0,1% Buffer

#### ➕ NEU: Setup A – Long (Pullback in Aufwärtstrend):
1. **4H:** Preis über 200 EMA, 50 EMA über 200 EMA
2. **4H:** Pullback zum 20 EMA (Preis berührt oder durchsticht 20 EMA)
3. **15m:** Impulskerze nach oben sichtbar
4. **15m:** Pullback bildet **Higher Low** (über dem 4H 20 EMA)
5. **15m:** Break über das letzte Swing-Hoch → **Entry**
6. **Stop:** Unter dem Higher Low − 0,1% Buffer

---

## 5. Setup B – Trendfortsetzung

### 🔴 SCHWACHSTELLE: "Nur mit Platz" – nicht definiert

**Problem:** "Platz" ist subjektiv. Wie viel Abstand zum nächsten Level ist genug?

### 🟡 OPTIMIERT: Beide Richtungen + messbare "Platz"-Regel

#### Setup B – Short:
1. **4H:** Klar unter 200 EMA
2. **Impuls nach unten → Konsolidierung (Range)**
3. **Break unter Konsolidierungs-Tief** → Entry
4. **Stop:** Über Konsolidierungs-Hoch + 0,1% Buffer

#### ➕ NEU: Setup B – Long:
1. **4H:** Klar über 200 EMA
2. **Impuls nach oben → Konsolidierung (Range)**
3. **Break über Konsolidierungs-Hoch** → Entry
4. **Stop:** Unter Konsolidierungs-Tief − 0,1% Buffer

#### 🟡 "Platz"-Regel (messbar):
- **Minimum R:R = 2:1** zum nächsten Support/Resistance-Level
- Nächstes Level identifizieren auf 4H (vorheriges Swing-Hoch/Tief, Orderblock, Liquiditätszone)
- Abstand Entry → Level < 2× Stop-Distanz → **SKIP**

---

## 6. Setup C – Bounce Filter

### 🟢 ORIGINAL GUT (Grundidee)

### 🟡 OPTIMIERT: Beide Richtungen + klare Gewichtung

#### Short-Filter (kein Short wenn ≥3 von 5 zutreffen):
| # | Kriterium | Gewicht |
|---|---|---|
| 1 | Support hält (mind. 2 Tests) | 1 |
| 2 | Higher Low auf 15m/1H | 1 |
| 3 | EMA Reclaim (Preis schließt über 20 EMA) | 1 |
| 4 | Lange untere Wicks (≥3 Kerzen) | 1 |
| 5 | Volumen steigt bei Bounces | 1 |

**Score ≥ 3 → Kein Short**

#### ➕ NEU: Long-Filter (kein Long wenn ≥3 von 5 zutreffen):
| # | Kriterium | Gewicht |
|---|---|---|
| 1 | Resistance hält (mind. 2 Tests) | 1 |
| 2 | Lower High auf 15m/1H | 1 |
| 3 | EMA Rejection (Preis prallt von 20 EMA ab) | 1 |
| 4 | Lange obere Wicks (≥3 Kerzen) | 1 |
| 5 | Volumen steigt bei Rejections | 1 |

**Score ≥ 3 → Kein Long**

---

## 7. Trade Management

### 🔴 SCHWACHSTELLE: Nur "30% bei 1R, Rest laufen lassen" – zu vage

**Probleme:**
- Was passiert mit den 70%? Wann wird der Rest geschlossen?
- "Stop nach Struktur trailen" – welche Struktur?
- Kein Break-Even-Regel
- Kein Zeitlimit

### 🟡 OPTIMIERT: Stufenplan

| Stufe | Preis bei… | Aktion |
|---|---|---|
| 1 | **+1R** | 30% schließen, Stop auf Entry (Break-Even) |
| 2 | **+1,5R** | Stop auf +0,5R trailen |
| 3 | **+2R** | Weitere 30% schließen (60% gesamt geschlossen) |
| 4 | **+3R** | Stop auf +1,5R trailen |
| 5 | **+4R oder Erschöpfung** | Alles schließen |

#### Trail-Regel (präzise):
- Nach 1R: Stop folgt dem **letzten 15m Higher Low** (Long) bzw. **Lower High** (Short)
- Nie weiter als 1,5× ATR(14, 15m) vom aktuellen Preis entfernt
- **Zeitlimit:** Wenn nach 48h kein +2R erreicht → Position evaluieren und ggf. schließen

---

## 8. Volumen

### 🔴 SCHWACHSTELLE: "Optional" ist zu schwach

Bei Krypto ist Volumen ein **Schlüsselindikator** für echte Breakouts vs. Fakeouts.

### 🟡 OPTIMIERT: Volumen als Pflicht-Bestätigung

- **Break mit überdurchschnittlichem Volumen** (> 1,5× Durchschnitt der letzten 20 Kerzen) = **A-Grade Setup** → volle Positionsgröße
- **Break mit normalem Volumen** = **B-Grade Setup** → 50% Positionsgröße
- **Break mit unterdurchschnittlichem Volumen** = **SKIP** (Fakeout-Risiko zu hoch)

---

## 9. Skip-Regeln

### 🟢 ORIGINAL GUT (Basis)

### 🟡 OPTIMIERT: Erweitert und priorisiert

| # | Skip-Regel | Priorität |
|---|---|---|
| 1 | EMA flach (ADX < 20) | **HARD SKIP** |
| 2 | Kein Platz (R:R < 2:1) | **HARD SKIP** |
| 3 | Setup C aktiv (Bounce-Score ≥ 3) | **HARD SKIP** |
| 4 | Chaotischer Markt (große Wicks, kein Trend) | **HARD SKIP** |
| 5 | ➕ **Daily Loss-Limit erreicht** (siehe §11) | **HARD SKIP** |
| 6 | ➕ **Funding Rate > 0,05%** gegen Trade-Richtung | **SOFT SKIP** (reduzierte Größe) |
| 7 | ➕ **Innerhalb 30min vor/nach Funding** (8h-Zyklus) | **SOFT SKIP** |
| 8 | ➕ **News-Event in < 2h** (FOMC, CPI, etc.) | **HARD SKIP** |
| 9 | ➕ **Wochenende Sonntag 18-24 Uhr** (dünne Liquidität) | **SOFT SKIP** |

---

## 10. Flow (Entscheidungsbaum)

### 🟢 ORIGINAL GUT

### 🟡 OPTIMIERT: Erweiterter Flow mit Checkpoints

```
1. TREND     → 4H: Über/Unter 200 EMA? ADX > 20?
                 ↓ Nein → STOP
2. LOCATION  → Wo sind die nächsten S/R-Levels? Genug Platz (R:R ≥ 2)?
                 ↓ Nein → STOP
3. SETUP     → A (Pullback) oder B (Trendfortsetzung) vorhanden?
                 ↓ Nein → STOP
4. FILTER    → Setup C Bounce-Score < 3? Keine Skip-Regel aktiv?
                 ↓ Nein → STOP
5. VOLUMEN   → Break-Volumen > 1,5× Durchschnitt? (A/B-Grade?)
                 ↓ C-Grade → STOP
6. RISIKO    → Positionsgröße berechnet? Stop gesetzt? Max 2 Positionen?
                 ↓ Check failed → STOP
7. ENTRY     → Order platzieren (Limit am Retest bevorzugt)
8. MANAGE    → Stufenplan §7 ausführen
```

---

## ➕ 11. NEU: Drawdown-Schutz (im Original komplett fehlend)

> 🔴 **Dies ist die größte Lücke im Original.** Ohne Drawdown-Regeln kann ein schlechter Tag/Woche das Konto zerstören – besonders bei 3x Hebel.

| Regel | Trigger | Aktion |
|---|---|---|
| **Daily Stop** | -1,5% Kontoverlust am Tag | Kein weiterer Trade heute |
| **Weekly Stop** | -3% Kontoverlust in der Woche | Nur noch A-Grade Setups |
| **Monthly Breaker** | -5% Kontoverlust im Monat | Trading-Pause 48h, Regelwerk reviewen |
| **Equity Breaker** | -10% vom Allzeithoch des Kontos | Hebel auf 1x reduzieren bis Recovery |

---

## ➕ 12. NEU: Funding Rate Awareness

> Bei 3x Hebel können Funding Rates erheblich kosten.

- **Funding > +0,03% (Long) / < -0,03% (Short):** Einkalkulieren in R:R
- **Funding > +0,05%:** Kein neuer Long (überfüllte Seite)
- **Funding < -0,05%:** Kein neuer Short
- **Funding-Zeiten:** Alle 8h (00:00, 08:00, 16:00 UTC) → Kein Entry 30min davor/danach

---

## ➕ 13. NEU: Entry-Typ Spezifikation

> Original sagt nicht, ob Market oder Limit Order.

- **Bevorzugt: Limit-Order am Retest** des Break-Levels (besserer Fill, weniger Slippage)
- **Market-Order nur** bei starkem Momentum + A-Grade Volumen + klarem Break
- **Maximale Slippage:** 0,1% – wenn mehr, Order canceln

---

## ➕ 14. NEU: Journal & Review-Prozess

- **Jeder Trade:** Screenshot (Entry, Management, Exit) + Setup-Typ + R-Ergebnis notieren
- **Wöchentlich:** Win-Rate, Avg-R, größter Drawdown, Setup-Verteilung reviewen
- **Monatlich:** Regelwerk anpassen basierend auf Daten (nicht Gefühl)
- **Mindestens 50 Trades** bevor Regeländerungen vorgenommen werden (statistische Relevanz)

---

## Merksätze

🟢 **Original beibehalten:**
- Location > Setup
- Verluste klein, Gewinner groß
- Kein Setup = kein Trade

🟡 **Erweitert:**
- **Kein Drawdown-Plan = kein echtes System**
- **Volumen bestätigt, Preis allein lügt**
- **Funding frisst Gewinne bei 3x – immer prüfen**
- **50 Trades vor jeder Regeländerung**

---

## Changelog V3 → V3-OPTIMIERT

| # | Änderung | Typ |
|---|---|---|
| 1 | Positionsgrößen-Formel mit Hebel-Korrektur | 🔴 Fix |
| 2 | Long-Setups für A und B ergänzt | 🔴 Fix |
| 3 | "Flach" messbar definiert (ADX + EMA-Steigung) | 🔴 Fix |
| 4 | "Platz" messbar definiert (R:R ≥ 2:1) | 🔴 Fix |
| 5 | Trade-Management Stufenplan statt vage Regeln | 🟡 Upgrade |
| 6 | Volumen von optional zu Pflicht | 🟡 Upgrade |
| 7 | Skip-Regeln erweitert (Funding, News, Liquidität) | 🟡 Upgrade |
| 8 | 50 EMA als zweiter Trendfilter | 🟡 Upgrade |
| 9 | Drawdown-Schutz komplett neu | ➕ Neu |
| 10 | Funding Rate Awareness | ➕ Neu |
| 11 | Entry-Typ Spezifikation | ➕ Neu |
| 12 | Long-Filter (Setup C Gegenstück) | ➕ Neu |
| 13 | Journal & Review-Prozess | ➕ Neu |
| 14 | Max. 2 gleichzeitige Positionen | ➕ Neu |
| 15 | Min Stop 0,5%, Max Stop 2,0% + ATR-Bezug | 🟡 Upgrade |
