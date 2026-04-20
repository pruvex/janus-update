from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

class HairPlugin(BaseVisionPlugin):
    @property
    def name(self): return "Hair"

    @property
    def clip_labels(self):
        return [
            # Haarfarben (Redhead-Boost + Blonde-Boost + Jet-Black-Boost)
            "auburn hair", "copper hair", "chestnut hair", "reddish brown hair",
            "bright red hair", "strawberry blonde", "light auburn hair",  # Redhead-Boost: Bright light variants
            "black hair", "dark brown hair", "brown hair", "grey hair", "silver hair",
            "jet black hair", "glossy black hair", "raven black hair",  # Jet-Black-Boost für Glanz
            "blonde hair", "platinum blonde hair", "golden blonde hair", "honey blonde hair",  # Blonde-Boost
            # Schatten-Labels (Cluster 2 Fix)
            "shadow in dark hair", "strong highlights on black hair", "overexposed highlights",
            # Haarstrukturen (Locken-Priorität)
            "curly hair", "defined curls", "voluminous curls", 
            "voluminous curly hair", "corkscrew curls", # <--- WICHTIG: Hier fehlte eins!
            "wavy hair", "straight hair", "bald",
            "frizzy curls", "black curly hair", "dense curls",
            # Bart-Erkennung (NEU für Cluster 2)
            "thick beard", "stubble", "goatee", "clean shaven", "mustache",
            "black beard", "grey beard", "brown beard", "red beard",
            # Haarlängen
            "long hair", "shoulder length", "shoulder-length", "medium hair",
            "bob cut", "pixie cut", "short hair"
        ]

    def evaluate(self, scores, context):
        results = []
        
        # --- 1. FARBE ---
        best_color = None  # V11: Initialisiere als None statt "unknown"
        color_score = 0.0
        
        # Aggressiver Dark-Hair-Check (Sherlock-Mode) - IMMER ausführen!
        dark_labels = ["black hair", "dark brown hair", "jet black hair", "raven black hair"]
        # Wir summieren die Scores aller dunklen Labels
        total_dark_score = sum(scores.get(l, 0.0) for l in dark_labels)
        
        # SYSTEM-ENTSCHEIDUNG:
        # Wenn die Summe der dunklen Signale > 0.0001 ist (praktisch immer vorhanden)
        # UND kein helles Signal (blonde/white) doppelt so stark ist...
        bright_labels = ["blonde hair", "white hair", "platinum blonde"]
        max_bright = max(scores.get(l, 0.0) for l in bright_labels)
        
        if total_dark_score > max_bright:
            context["is_dark_hair"] = True
            logger.info(f"SHERLOCK: Dunkle Haare erkannt (Dark Sum: {total_dark_score:.4f} > Bright Max: {max_bright:.4f})")
        else:
            context["is_dark_hair"] = False
            logger.info(f"SHERLOCK: Helle Haare erkannt (Dark Sum: {total_dark_score:.4f} <= Bright Max: {max_bright:.4f})")

        red_labels = ["auburn hair", "copper hair", "chestnut hair", "reddish brown hair",
                   "bright red hair", "strawberry blonde", "light auburn hair"]  # Redhead-Boost: Bright light variants
        dark_labels = ["black hair", "dark brown hair"]
        grey_labels = ["grey hair", "silver hair"]
        blonde_labels = ["blonde hair", "platinum blonde hair", "golden blonde hair", "honey blonde hair"]  # Blonde-Boost
        
        # Scores ermitteln
        best_red = max(red_labels, key=lambda l: scores.get(l, 0.0))
        red_score = scores.get(best_red, 0.0)
        
        best_dark = max(dark_labels, key=lambda l: scores.get(l, 0.0))
        dark_score = scores.get(best_dark, 0.0)
        
        best_grey = max(grey_labels, key=lambda l: scores.get(l, 0.0))
        grey_score = scores.get(best_grey, 0.0)
        
        best_blonde = max(blonde_labels, key=lambda l: scores.get(l, 0.0))
        blonde_score = scores.get(best_blonde, 0.0)

        all_color_labels = red_labels + dark_labels + grey_labels + blonde_labels
        ranked_color_scores = sorted(
            [(label, float(scores.get(label, 0.0))) for label in all_color_labels],
            key=lambda item: item[1],
            reverse=True,
        )
        top_color_score = ranked_color_scores[0][1] if ranked_color_scores else 0.0
        second_color_score = ranked_color_scores[1][1] if len(ranked_color_scores) > 1 else 0.0
        top_margin = top_color_score - second_color_score
        
        # Forensik: Top 3 lokale Softmax-Scores für Bild 1-1
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_scores[:3]
        logger.info(f"FORENSIK Top 3 Scores: {top_3}")
        
        # Entscheidungslogik (Redhead-Boost - Diamond-Standard + Spezifitäts-Kontrolle)
        # Spezifitäts-Gewichtung: Wenn auburn/reddish brown > 0.15 UND Top-Position oder max 10% hinter Braun
        specific_red_score = max(scores.get("auburn hair", 0.0), scores.get("reddish brown hair", 0.0))
        dark_brown_score = scores.get("dark brown hair", 0.0)
        
        # Prüfe ob rotes Signal Top-Position hat oder maximal 10% hinter Braun liegt
        red_is_top_or_close = False
        if specific_red_score > 0.15:
            if specific_red_score >= dark_brown_score:
                red_is_top_or_close = True  # Top-Position
            elif dark_brown_score > 0 and specific_red_score >= dark_brown_score * 0.9:
                red_is_top_or_close = True  # Max 10% hinter Braun
        
        if red_is_top_or_close:
            red_score = red_score + 0.2  # Bonus gegen generisches dark brown
            logger.info(f"REDHEAD-BONUS: {specific_red_score:.4f} > 0.15, Top/Close -> +0.2 = {red_score:.4f}")
        else:
            logger.info(f"KEIN REDHEAD-BONUS: {specific_red_score:.4f}, nicht Top/Close zu Braun ({dark_brown_score:.4f})")
        
        if red_score > 0.12 and red_score > (blonde_score * 1.4) and red_score > (dark_score * 1.4):
            best_color = best_red
            color_score = red_score
            logger.info(f"Redhead-Boost aktiv: {best_red} ({red_score:.4f}) > 0.12")
        # Blonde-Boost V11: Wenn blonde_score > 0.001 (reduzierte Sensibilität) UND dark_score < 0.001, dann setze die Farbe auf "blonden"
        elif blonde_score > 0.001 and dark_score < 0.001:  # Blonde-Schwelle erhöht (0.0002 -> 0.001)
            best_color = best_blonde
            color_score = blonde_score
            context["blonde_hair_detected"] = True  # V11: Kontext für Perlen-Erkennung
            logger.info(f"Blonde-Boost V11 aktiv: {best_blonde} ({blonde_score:.4f}) > 0.001, dark_score {dark_score:.4f} < 0.001")
        elif dark_score > 0.001 and grey_score < 0.01:  # Elena-Fall: Dunkel gewinnt gegen schwaches Grau (Sigmoid angepasst)
            # Elena-Fall: Dunkel gewinnt gegen schwaches Grau (Reflexion)
            best_color = best_dark
            color_score = dark_score
            context["is_dark_hair"] = True
        elif grey_score > 0.02:  # Graue Haar Schwelle für Sigmoid-Skalierung angepasst (0.008 -> 0.02)
            best_color = best_grey
            color_score = grey_score
            # NEU: Graue Haar Optimierung für Cluster 3
            # Verhindere, dass graue Haar bei älteren Personen als "Reflexion" unterdrückt wird
            if context.get("has_pattern", False):  # Wenn Muster vorhanden (ältere Person)
                logger.info(f"👴 Grey-Hair-Optimierung: {best_grey} ({grey_score:.4f}) bei Muster-Erkennung bestätigt")
            # Classic Blonde-Boost (Fallback)
        elif scores.get("blonde hair", 0.0) > 0.002:  # Blonde-Boost: Schwelle für Blond
            best_color = "blonde hair"
            color_score = scores.get("blonde hair", 0.0)
            logger.info(f"Classic Blonde-Boost aktiv: blonde hair ({color_score:.4f}) > 0.002")
        else:
            # Fallback: Nur wenn Score über Minimal-Threshold liegt
            all_colors = red_labels + dark_labels + grey_labels + blonde_labels
            best_color = max(all_colors, key=lambda l: scores.get(l, 0.0))
            color_score = scores.get(best_color, 0.0)
            
            # Aggressiver Dark-Hair-Check (Sherlock-Mode)
            dark_labels = ["black hair", "dark brown hair", "jet black hair", "raven black hair"]
            # Wir summieren die Scores aller dunklen Labels
            total_dark_score = sum(scores.get(l, 0.0) for l in dark_labels)
            
            # SYSTEM-ENTSCHEIDUNG:
            # Wenn die Summe der dunklen Signale > 0.0001 ist (praktisch immer vorhanden)
            # UND kein helles Signal (blonde/white) doppelt so stark ist...
            bright_labels = ["blonde hair", "white hair", "platinum blonde"]
            max_bright = max(scores.get(l, 0.0) for l in bright_labels)
            
            if total_dark_score > max_bright:
                context["is_dark_hair"] = True
                logger.info(f"🎯 SHERLOCK: Dunkle Haare erkannt (Dark Sum: {total_dark_score:.4f} > Bright Max: {max_bright:.4f})")
            else:
                context["is_dark_hair"] = False
                logger.info(f"🎯 SHERLOCK: Helle Haare erkannt (Dark Sum: {total_dark_score:.4f} <= Bright Max: {max_bright:.4f})")
            
            # Dark-Hair Priority (Cluster 2 Fix): Bevorzuge schwarze/dunkle Haare über graue
            # Vereinfachte Logik ohne age_group Abhängigkeit
            if best_color in ["grey hair", "silver hair"]:
                # Jet-Black-Boost: Prüfe glänzende schwarze Haare
                jet_black_score = max([scores.get("jet black hair", 0.0), 
                                     scores.get("glossy black hair", 0.0), 
                                     scores.get("raven black hair", 0.0)])
                
                black_score = scores.get("black hair", 0.0)
                dark_brown_score = scores.get("dark brown hair", 0.0)
                dark_score = max(black_score, dark_brown_score, jet_black_score)
                
                # Wenn dunkle Haare erkennbar sind, bevorzuge sie über graue
                if dark_score > 0.001:
                    best_color = "jet black hair" if jet_black_score >= max(black_score, dark_brown_score) else ("black hair" if black_score >= dark_brown_score else "dark brown hair")
                    color_score = dark_score
                    logger.info(f"🌑 Dark-Hair Priority: {best_color} ({color_score:.4f}) über grey hair ({scores.get('grey hair', 0.0):.4f})")
                else:
                    best_color = "grey hair"  # Behalte graue Haare wenn keine dunkle Alternative
                    color_score = scores.get('grey hair', 0.0)
                    if dark_score > color_score * 0.5:  # 50% Regel: Dunkel muss nicht viel schlechter sein
                        best_color = "jet black hair" if jet_black_score >= max(black_score, dark_brown_score) else ("black hair" if black_score >= dark_brown_score else "dark brown hair")
                        color_score = dark_score
                        logger.info(f"🌑 Dark-Hair Priority: {best_color} ({color_score:.4f}) über grey hair ({scores.get('grey hair', 0.0):.4f})")
            
            # Fallback-Korrektur V11: Verhindere "Dunkelbraun"-Fallback, wenn alle Scores 0.0 sind
            if color_score <= 0.0000:
                best_color = None
                color_score = 0.0
                logger.info(f"💇 Fallback-Korrektur V11: Alle Scores 0.000, verwende None statt 'dunkelbraunen'")
            # Null-Score-Verbot: Wenn das stärkste Farbauswahl-Label einen Score von 0.0000 hat, gib keine Farbe zurück
            elif color_score <= 0.0000:
                best_color = "unknown"
                color_score = 0.0
                logger.info(f"💇 Null-Score-Verbot: Score {color_score:.4f} <= 0.0000, REJECTED")
            # Fallback-Guard: Score unter 0.0001 muss immer zu REJECTED führen
            elif color_score < 0.0001:
                best_color = "unknown"
                color_score = 0.0
                logger.info(f"💇 Fallback-Guard: Score {color_score:.4f} < 0.0001, REJECTED")
            # Nur verwenden, wenn Score über Minimal-Threshold (0.001)
            elif color_score < 0.001:
                best_color = "unknown"
                color_score = 0.0
                logger.info(f"💇 Fallback-Block: Alle Scores unter 0.001, behalte 'unknown'")

        if best_color in ["grey hair", "silver hair"]:
            if dark_score >= max(grey_score * 0.75, 0.03):
                best_color = best_dark
                color_score = dark_score
                context["is_dark_hair"] = True
                logger.info(
                    "Grey rebalance -> dark: %s (dark=%.4f, grey=%.4f)",
                    best_color,
                    dark_score,
                    grey_score,
                )
            elif (not context.get("is_dark_hair", False)) and blonde_score >= max(grey_score * 0.85, 0.03):
                best_color = best_blonde
                color_score = blonde_score
                context["blonde_hair_detected"] = True
                logger.info(
                    "Grey rebalance -> blonde: %s (blonde=%.4f, grey=%.4f)",
                    best_color,
                    blonde_score,
                    grey_score,
                )

        if color_score < 0.006 or (color_score < 0.02 and top_margin < 0.0015):
            best_color = None
            color_score = 0.0
            logger.info(
                "Hair color withheld due weak margin/confidence (top=%.4f, second=%.4f, margin=%.4f)",
                top_color_score,
                second_color_score,
                top_margin,
            )

        # Status-Bestimmung mit Fallback-Guard V11
        if best_color is None or color_score < 0.001:
            status = "UNSICHER"  # Wenn None oder kein Score über 0.001
        else:
            status = "SICHER"
        
        results.append(FeatureResult("HAARFARBE", best_color, status, color_score))

        # --- 2. STRUKTUR ---
        curly_labels = [
            "curly hair", "defined curls", "voluminous curls", 
            "voluminous curly hair", "corkscrew curls", 
            "frizzy curls", "black curly hair", "dense curls"
        ]
        other_labels = ["wavy hair", "straight hair", "bald"]
        
        best_curly = max(curly_labels, key=lambda l: scores.get(l, 0.0))
        curly_score = scores.get(best_curly, 0.0)
        
        best_other = max(other_labels, key=lambda l: scores.get(l, 0.0))
        other_score = scores.get(best_other, 0.0)
        
        # Elena-Boost: Wenn "voluminous" oder "dense" erkannt wird, pushe Locken
        voluminous_bonus = 0.0
        if "voluminous" in best_curly or "dense" in best_curly:
            if curly_score > 0.003: # Nur boosten wenn Signal da ist
                voluminous_bonus = 0.004
        
        # Vergleich mit Toleranz (Locken sollen nicht zu oft false-positive gewinnen)
        final_curly_score = curly_score + voluminous_bonus
        
        curly_margin = 1.05
        if final_curly_score < 0.06:
            curly_margin = 1.2

        if final_curly_score > other_score * curly_margin:
            best_struct = best_curly
            struct_score = final_curly_score
        else:
            best_struct = best_other
            struct_score = other_score
            
        # Status
        status = "REJECTED"
        if struct_score > 0.012: status = "SICHER"
        elif struct_score > 0.006: status = "WAHRSCHEINLICH"
        
        # Kontext setzen für Brillen-Plugin (WICHTIG!)
        # Wir setzen hair_type nur, wenn die Struktur wirklich dominiert (reduziert False-Positives)
        if best_struct in curly_labels and struct_score > 0.02:
            context["hair_type"] = "curly"
            logger.info(f"Locken-Prioritaet aktiv: {best_curly} ({curly_score:.4f})")
        elif "wavy" in best_struct and struct_score > 0.02:
            context["hair_type"] = "wavy"
        elif "straight" in best_struct and struct_score > 0.02:
            context["hair_type"] = "straight"

        results.append(FeatureResult("HAAR_STRUKTUR", best_struct, status, struct_score))

        # --- 3. FRISUR / Haarlänge als sekundäres Merkmal ---
        length_labels = [
            "long hair",
            "shoulder length",
            "shoulder-length",
            "medium hair",
            "short hair",
            "bob cut",
            "pixie cut",
        ]
        length_scores = {label: scores.get(label, 0.0) for label in length_labels}
        best_length = max(length_scores, key=length_scores.get)
        best_length_score = length_scores.get(best_length, 0.0)
        if best_length_score > 0.02:
            length_status = "WAHRSCHEINLICH"
        else:
            length_status = "HINWEIS"
        results.append(FeatureResult("FRISUR", best_length, length_status, best_length_score))
        
        # --- 3. BART-ERKENNUNG (NEU für Cluster 2) ---
        beard_labels = ["thick beard", "stubble", "goatee", "clean shaven", "mustache",
                         "black beard", "grey beard", "brown beard", "red beard"]
        best_beard = max(beard_labels, key=lambda l: scores.get(l, 0.0))
        beard_score = scores.get(best_beard, 0.0)

        gender = str(context.get("gender", "")).lower()
        is_color_beard = best_beard in ["black beard", "grey beard", "brown beard", "red beard"]
        threshold = 0.01
        if is_color_beard:
            threshold = 0.006
        if gender == "woman":
            threshold = max(threshold, 0.02)

        if "has_beard" not in context:
            if beard_score > threshold:  # Bart-Schwelle
                context["has_beard"] = True
                context["beard_style"] = best_beard
                beard_status = "WAHRSCHEINLICH"
                logger.info(f"🧔 Bart-Erkennung: {best_beard} ({beard_score:.4f}) > 0.01 = {beard_status}")
                results.append(FeatureResult("BART", best_beard, beard_status, beard_score))
            else:
                context["has_beard"] = False
                context["beard_style"] = None
        else:
            # If beard context is already set (e.g., by BeardPlugin), still emit beard color info
            # so downstream mapping can produce BART color (Cluster 2), without overriding style.
            if is_color_beard and beard_score > threshold:
                beard_status = "WAHRSCHEINLICH"
                logger.info(f"🧔 Bart-Farbe (non-invasive): {best_beard} ({beard_score:.4f}) > {threshold:.3f} = {beard_status}")
                results.append(FeatureResult("BART", best_beard, beard_status, beard_score))
        
        # Farb-Kontext finalisieren
        if isinstance(best_color, str) and ("black" in best_color or "dark" in best_color):
             context["is_dark_hair"] = True
             logger.info(f"🎨 Dark-Hair-Context gesetzt: {best_color}")

        return results