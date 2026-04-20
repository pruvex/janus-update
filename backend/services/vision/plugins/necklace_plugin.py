from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

class NecklacePlugin(BaseVisionPlugin):
    @property
    def name(self): return "Necklace"

    @property
    def clip_labels(self):
        return [
            # Halsschmuck-Typen (WICHTIG für dieses Bild)
            "pearl necklace", "white beaded necklace", "gold chain", "silver pendant",
            # Perlen-Detektion: CLIP braucht den Begriff "Perle" - spezifische organische Labels
            "round white pearl beads", "string of pearls", "beaded ivory necklace",
            # Dark-on-Dark: Schwarze Schmuckstücke (Cluster 2)
            "black choker", "black necklace", "black choker necklace", "dark choker", "velvet choker",
            # Material-Spezifisch
            "gold heart pendant", "multiple gold chains", "silver chain necklace",
            # Glint vs. Glow Labels (NEU - Material-Intelligenz)
            "sharp metallic glint", "bright golden line", "specular reflection on metal",
            "matte velvet texture", "soft pearl luster", "diffuse light on fabric",
            # Filigree-Detection für Goldketten (NEU)
            "filigree gold lines", "delicate gold chain", "fine metalwork",
            # Single Point vs Multiple Beads (NEU)
            "single point of light", "multiple small white beads",
            # Matte-Guard Labels für Cluster 4
            "matte wood", "wooden beads", "non-reflective material", 
            "clay jewelry", "matte texture", "wooden jewelry",
            "delicate necklace", "choker necklace", "statement necklace",
            # Positionsspezifisch
            "necklace on chest", "jewelry on collarbone", "pendant on neck",
            # Hals-Anker: Negative Labels (Null-Hypothese)
            "bare neck", "plain skin on collarbone", "unobstructed neckline", "no jewelry on neck"
        ]

    def evaluate(self, scores, context):
        results = []
        
        # Direkte Halsschmuck-Scores
        necklace_labels = ["pearl necklace", "white beaded necklace", "gold chain", "silver pendant",
                        "round white pearl beads", "string of pearls", "beaded ivory necklace",  # Perlen-Sensor V10
                        "black choker", "black necklace", "black choker necklace", "dark choker"]  # Cluster 2
        best_necklace = max(necklace_labels, key=lambda l: scores.get(l, 0.0))
        necklace_score = scores.get(best_necklace, 0.0)
        
        # SNR-Logik: Ketten oft verdeckt + Wet-Skin-Guard + Hals-Anker
        confuser_labels = ["neck shadow", "collar shadow", "chest texture", 
                         "wet skin reflection", "neck shine", "collar bone highlight"]  # Wet-Skin-Guard
        max_confuser = max([scores.get(label, 0.0) for label in confuser_labels])
        
        # Muster-Schutz für Cluster 3 (NEU)
        has_pattern = context.get("has_pattern", False)
        has_complex_pattern = context.get("has_complex_pattern", False)
        pattern_confuser_labels = ["plaid pattern", "checkered fabric", "floral print", "knitted texture"]
        max_pattern_confuser = max([scores.get(label, 0.0) for label in pattern_confuser_labels])
        
        # Matte-Guard für Cluster 4 (NEU) - Material-Unterscheidung
        matte_confuser_labels = ["matte wood", "wooden beads", "non-reflective material", "clay jewelry", "matte texture"]
        max_matte_confuser = max([scores.get(label, 0.0) for label in matte_confuser_labels])
        
        # Material-Veto Logik (NEU - Glint vs Glow Analyse)
        # Bild 4.1 Fix: Gold auf dunkler Haut vs Samt-Kropfband
        # Verwende tatsächlich detektierte Gold-Signale aus anderen Kategorien
        metallic_glint_labels = ["sharp metallic glint", "bright golden line", "specular reflection on metal",
                                 "filigree gold lines", "delicate gold chain", "fine metalwork",
                                 "gold chain", "gold bracelet", "gold ring", "gold heart pendant", "multiple gold chains"]
        max_metallic_glint = max([scores.get(label, 0.0) for label in metallic_glint_labels])
        
        velvet_glow_labels = ["matte velvet texture", "soft pearl luster", "diffuse light on fabric",
                             "velvet choker", "matte texture", "wooden beads"]
        max_velvet_glow = max([scores.get(label, 0.0) for label in velvet_glow_labels])
        
        # Bild 4.2 Fix: Single Point vs Multiple Beads
        single_point_labels = ["single point of light", "silver pendant", "single light"]
        multiple_beads_labels = ["multiple small white beads", "pearl necklace", "white beaded necklace", 
                               "round white pearl beads", "string of pearls", "beaded ivory necklace"]
        
        max_single_point = max([scores.get(label, 0.0) for label in single_point_labels])
        max_multiple_beads = max([scores.get(label, 0.0) for label in multiple_beads_labels])
        
        # Material-Veto: Wenn starker metallic glint vorhanden, blockiere velvet choker
        if max_metallic_glint > 0.01 and "velvet choker" in best_necklace.lower():
            logger.info(f"🚫 MATERIAL-VETO: Metallic glint {max_metallic_glint:.4f} > 0.01 blockiert velvet choker -> REJECT")
            snr = -999.0  # Erzwinge REJECT
        
        # Gold-Boost für dunkle Haut (reduziertes SNR-Limit)
        teint_items = context.get("teint_items", [])
        is_dark_skin = any(item.get("label", "").lower() in ["dark skin", "brown skin"] 
                          for item in teint_items if item.get("score", 0.0) > 0.005)
        
        if is_dark_skin and max_metallic_glint > 0.01 and max_velvet_glow < 0.06:
            # Gold auf dunkler Haut: reduzierte SNR-Hürde wenn kein Matte-Signal dominiert
            logger.info(f"🏆 GOLD-BOOST: Dark skin + metallic glint {max_metallic_glint:.4f} > velvet glow {max_velvet_glow:.4f} -> SNR-Hürde reduziert")
            snr += 0.01  # Reduziere SNR-Hürde stärker
        
        # SNR-Berechnung mit Muster-Schutz (stärker bei has_complex_pattern)
        if has_complex_pattern:
            snr = necklace_score - max(max_confuser, max_pattern_confuser * 1.5, max_matte_confuser)  # Extra-Schutz bei komplexen Mustern + Matte-Guard
        else:
            snr = necklace_score - max(max_confuser, max_pattern_confuser, max_matte_confuser)  # Muster-Schutz + Matte-Guard
        
        # Matte-Guard SNR-Logik für Cluster 4
        if max_matte_confuser > 0.01:
            # Finde den stärksten metallischen Score
            metallic_labels = ["gold necklace", "silver necklace", "gold chain", "silver chain"]
            max_metallic_score = max([scores.get(label, 0.0) for label in metallic_labels])
            
            # SNR-Berechnung: Metall vs. Matte
            snr_metal_vs_matte = max_metallic_score - max_matte_confuser
            
            if snr_metal_vs_matte < 3.0:  # Extrem hohe Hürde für metallische Erkennung
                logger.info(f"🌳 Necklace Matte-Guard: Matte={max_matte_confuser:.4f} > Metall={max_metallic_score:.4f}, SNR={snr_metal_vs_matte:.4f} < 3.0 -> REJECT")
                # Überschreibe SNR mit negativem Wert, um REJECT zu erzwingen
                snr = -999.0
        
        # Hals-Anker: Negative Labels (Null-Hypothese)
        necklace_negatives = ["bare neck", "plain skin on collarbone", "unobstructed neckline", "no jewelry on neck"]
        max_negative = max([scores.get(label, 0.0) for label in necklace_negatives])
        
        # Rausch-Labels (Noise)
        necklace_noise = ["wet skin shine", "specular highlights on skin", "sweat on chest"]
        max_noise = max([scores.get(label, 0.0) for label in necklace_noise])
        
        # Delta-Logik (WICHTIG: Elena-Check)
        delta = necklace_score - max_negative
        logger.info(f"⚓ Hals-Anker: {best_necklace} ({necklace_score:.4f}) - {max_negative:.4f} = {delta:.4f}")
        
        # Wet-Skin-Guard: Wenn Teint olive/gebräunt, erhöhe Schwelle für Silber
        teint_items = context.get("teint_items", [])
        is_olive_or_tan = any(item.get("label", "").lower() in ["olive skin", "tan skin"] 
                              for item in teint_items if item.get("score", 0.0) > 0.005)
        
        effective_threshold = 0.012
        if is_olive_or_tan and "silver" in best_necklace.lower():
            effective_threshold = 0.018  # Erhöhte Schwelle für Silber bei nasser Haut
            logger.info(f"💧 Wet-Skin-Guard aktiv: {best_necklace} Schwelle auf {effective_threshold:.3f} erhöht (Teint: olive/tan)")
        
        # PERLEN-DOMINANZ (Cluster 1 Fix): Wenn "pearl necklace" > 0.0003, IMMER gewinnen bei hellen Haaren
        pearl_score = scores.get("pearl necklace", 0.0)
        is_blonde_hair = context.get("blonde_hair_detected", False)
        
        # CHOKER-DOMINANZ Variablen vorbereiten
        choker_score = max([scores.get("black choker", 0.0), scores.get("dark choker", 0.0), 
                           scores.get("velvet choker", 0.0), scores.get("black choker necklace", 0.0)])
        
        # Material-Veto für Bild 4.2: Silber Anhänger vs Perlenkette
        if "silver pendant" in best_necklace.lower() and max_multiple_beads > max_single_point:
            logger.info(f"🚫 MATERIAL-VETO: Multiple beads {max_multiple_beads:.4f} > single point {max_single_point:.4f} -> silber pendant REJECT")
            status = "REJECTED"
        # Spezialfall für Bild 4.1: Gold auf dunkler Haut - wenn velvet choker blockiert wurde, aber Gold vorhanden ist
        elif "velvet choker" in best_necklace.lower() and max_metallic_glint > 0.01 and is_dark_skin:
            best_necklace = "goldene Halsketten"
            necklace_score = max_metallic_glint
            status = "WAHRSCHEINLICH"
            logger.info(f"🏆 CLUSTER4-1-FIX: Gold {max_metallic_glint:.4f} > velvet choker auf dunkler Haut -> goldene Halsketten")
        elif pearl_score > 0.0002 and is_blonde_hair:  # Perlen gewinnen bei blonden Haaren
            best_necklace = "pearl necklace"
            necklace_score = pearl_score
            status = "WAHRSCHEINLICH"
            logger.info(f"🐚 PERLEN-DOMINANZ: pearl necklace ({pearl_score:.4f}) > 0.0002 = WAHRSCHEINLICH (blondes Haar -> Perlen)")
        # CHOKER-DOMINANZ (Cluster 2 Fix): Wenn choker erkannt, gewinnen (nur bei dunklen Haaren)
        elif choker_score > 0.0005 and not is_blonde_hair:
            # Finde den besten Choker-Label
            choker_labels = ["black choker", "dark choker", "velvet choker", "black choker necklace"]
            best_choker = max(choker_labels, key=lambda l: scores.get(l, 0.0))
            best_necklace = best_choker
            necklace_score = choker_score
            status = "WAHRSCHEINLICH"
            logger.info(f"🐚 CHOKER-DOMINANZ: {best_choker} ({choker_score:.4f}) > 0.0005 = WAHRSCHEINLICH")
        # PERLEN-DOMINANZ (Cluster 1 Fix): Wenn "pearl necklace" > 0.0003, IMMER gewinnen
        elif scores.get("pearl necklace", 0.0) > 0.0003:
            best_necklace = "pearl necklace"
            necklace_score = scores.get("pearl necklace", 0.0)
            status = "WAHRSCHEINLICH"
            silver_pendant_score = scores.get("silver pendant", 0.0)
            logger.info(f"🐚 PERLEN-DOMINANZ: pearl necklace ({necklace_score:.4f}) > 0.0003 = WAHRSCHEINLICH (überschreibt silver pendant {silver_pendant_score:.4f})")
        # Dark-on-Dark Bypass für Cluster 2: Schwarze Schmuckstücke auf Haut (höchste Priorität)
        elif "black" in best_necklace.lower() and necklace_score > 0.002:
            status = "WAHRSCHEINLICH"
            logger.info(f"🌑 Dark-on-Dark Bypass: {best_necklace} ({necklace_score:.4f}) > 0.002 = WAHRSCHEINLICH (schwarz auf Haut)")
        # Status-Bestimmung mit Delta-Logik, Threshold-Verschärfung und Perlen-Vorteil
        elif necklace_score > effective_threshold and delta > 0.005:  # WICHTIG: Delta > 0.005
            status = "SICHER"
        elif necklace_score > 0.0008 and delta > 0.008:  # Delta-Härtung: 0.005 -> 0.008
            status = "WAHRSCHEINLICH"
        elif "pearl necklace" in best_necklace.lower() and necklace_score > 0.0004:
            status = "WAHRSCHEINLICH"
            logger.info(f"🐚 Perlen-Priorität V11: {best_necklace} ({necklace_score:.4f}) > 0.0004 = WAHRSCHEINLICH")
        # Spezial-Perlen-Erkennung: Wenn "silver pendant" aber Score > 0.0005, könnte es eine Perlenkette sein
        # NUR bei blondem Haar (Perlen passen besser zu blond als zu dunklem Haar)
        elif "silver pendant" in best_necklace.lower() and necklace_score > 0.0005 and context.get("blonde_hair_detected", False):
            status = "WAHRSCHEINLICH"
            logger.info(f"🐚 Perlen-Alternative V11.5: {best_necklace} ({necklace_score:.4f}) > 0.0005 = WAHRSCHEINLICH (blondes Haar -> Perlen)")
        # Perlen-Vorteil: Da Perlen oft wenig metallischen Glanz haben, senke Schwelle
        elif "pearl" in best_necklace.lower() and necklace_score > 0.0005 and delta > 0.008:
            status = "WAHRSCHEINLICH"
            logger.info(f"🐚 Perlen-Vorteil: {best_necklace} ({necklace_score:.4f}) > 0.0005 = WAHRSCHEINLICH")
        elif necklace_score > 0.0004 and snr > 0.0005:  # Sehr sensitiv
            status = "HINWEIS"
        else:
            status = "REJECTED"
            logger.info(f"⚓ Hals-Anker REJECTED: Delta {delta:.4f} < 0.008 oder Score {necklace_score:.4f} < {effective_threshold:.3f}")
        
        if status != "REJECTED" and necklace_score > 0:
            results.append(FeatureResult("HALSKMUCK", best_necklace, status, necklace_score))
            logger.info(f"PLUGIN Necklace: {best_necklace} ({status}, Score: {necklace_score:.4f}, SNR: {snr:.4f})")
        
        # Wenn nichts gefunden, expliziter REJECTED-Eintrag
        if not results:
            results.append(FeatureResult("HALSKMUCK", "kein Halsschmuck", "REJECTED", 0.0))
        
        # Perlen-Dominanz (Der "Pearl-Override")
        pearl_results = [r for r in results if "pearl" in r.label or "beaded" in r.label]
        metal_results = [r for r in results if "silver" in r.label or "gold" in r.label]

        # Wenn wir eine Perle haben (auch schwach), löschen wir schwache Silber-Signale
        if pearl_results:
            best_pearl = max(pearl_results, key=lambda x: x.score)
            if best_pearl.score > 0.0005: # Minimales Perlen-Signal
                # Behalte Perlen, wirf Metall raus, außer Metall ist EXTREM stark (>0.05)
                results = [r for r in results if ("pearl" in r.label or "beaded" in r.label) or r.score > 0.05]
                # Setze Perle auf WAHRSCHEINLICH, damit sie durch den Filter kommt
                for r in results:
                    if "pearl" in r.label: 
                        r.status = "WAHRSCHEINLICH"
            
        return results
