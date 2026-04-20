from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

# DEFINITION DER SCHMUCK-CLUSTER (Ohrringe & Ketten ausgelagert)
JEWELRY_CLUSTERS = {
    "bracelet": [
        "gold bracelet", "silver bracelet", "beaded bracelet", "chain bracelet"
    ],
    "ring": [
        "gold ring", "silver ring", "diamond ring", "wedding ring"
    ],
    "brooch": [
        "decorative pin", "jewelry pin", "fabric brooch"
    ]
}

class JewelryPlugin(BaseVisionPlugin):
    @property
    def name(self): return "Jewelry"

    @property
    def feature_config(self):
        return {
            "bracelet": {
                "positive": [
                    "gold bracelet", "silver bracelet", "beaded bracelet", 
                    "chain bracelet", "shiny bracelet", "delicate bracelet"
                ]
            },
            "ring": {
                "positive": [
                    "gold ring", "silver ring", "diamond ring", 
                    "wedding ring", "engagement ring", "signet ring"
                ]
            },
            "brooch": {
                "positive": [
                    "decorative pin", "jewelry pin", "fabric brooch", 
                    "enamel pin", "metal brooch"
                ],
                "negative": [  # Matte-Guard Labels für Cluster 4
                    "matte wood", "wooden beads", "non-reflective material", 
                    "clay jewelry", "matte texture", "wooden jewelry"
                ]
            }
        }

    @property
    def clip_labels(self):
        # Direkte Schmuck-Labels (Ohrringe & Ketten entfernt)
        direct_labels = [
            # Armbänder
            "gold bracelet", "silver bracelet", "beaded bracelet", 
            "chain bracelet", "shiny bracelet", "delicate bracelet",
            # Ringe
            "gold ring", "silver ring", "diamond ring", 
            "wedding ring", "engagement ring", "signet ring",
            # Broschen
            "decorative pin", "jewelry pin", "fabric brooch", 
            "enamel pin", "metal brooch",
            # Halsketten
            "gold necklace", "silver necklace", "pearl necklace", 
            "chain necklace", "delicate necklace", "shiny necklace",
            # Matte-Guard Labels für Cluster 4 (NEU)
            "matte wood", "wooden beads", "non-reflective material", 
            "clay jewelry", "matte texture", "wooden jewelry"
        ]
        
        # Indirekte Labels (Reflexionen, Lichter)
        indirect_labels = ["metallic shine near ear", "unnatural reflection on chest", "point of light on earlobe", 
                        "shiny object on wrist", "glint on finger", "metallic reflection on chest"]
        
        return direct_labels + indirect_labels

    def evaluate(self, scores, context):
        results = []
        
        # Schal-Schutz (Scarf-Guard): Verhindert Fehlinterpretation von Karo-Mustern
        scarf_confuser_labels = [
            "plaid scarf", "checkered pattern", "knitted scarf", "wool texture", 
            "fringes on clothing", "striped fabric", "beige scarf"
        ]
        max_scarf_score = max([scores.get(label, 0.0) for label in scarf_confuser_labels])
        
        # Muster-Schutz für Cluster 3 (NEU)
        has_pattern = context.get("has_pattern", False)
        has_complex_pattern = context.get("has_complex_pattern", False)
        pattern_confuser_labels = ["plaid pattern", "checkered fabric", "floral print", "knitted texture"]
        max_pattern_score = max([scores.get(label, 0.0) for label in pattern_confuser_labels])
        
        # Matte-Guard für Cluster 4 (NEU) - Material-Unterscheidung
        matte_confuser_labels = ["matte wood", "wooden beads", "clay jewelry"]  # Nur spezifische Matte-Materialien
        max_matte_score = max([scores.get(label, 0.0) for label in matte_confuser_labels])
        
        # DEBUG: Matte-Guard Scores
        logger.info(f"🌳 Matte-Guard DEBUG: Matte Scores - {[f'{label}: {scores.get(label, 0.0):.4f}' for label in matte_confuser_labels]}")
        logger.info(f"🌳 Matte-Guard DEBUG: Max Matte Score = {max_matte_score:.4f}")
        
        # Basis-Noise-Floor (global)
        base_noise_floor = 0.0005
        
        # Muster-Schutz: Wenn has_complex_pattern aktiv ist, erhöhe DOMINANCE für Schmuck auf 2.2
        # (Wird pro Cluster berechnet, da noise_floor pro Cluster neu gesetzt wird)
        
        for cluster_name, config in self.feature_config.items():
            # PRO-CLUSTER Noise-Floor Berechnung
            noise_floor = base_noise_floor  # Jedes Cluster startet mit frischem Noise-Floor!
            
            # Direkte und indirekte Scores berechnen
            direct_scores = [scores.get(label, 0.0) for label in config["positive"] if label in config["positive"]]
            
            # Indirekte Labels (angepasst für neue Kategorien)
            indirect_labels = ["metallic shine near ear", "unnatural reflection on chest", "point of light on earlobe", 
                            "shiny object on wrist", "glint on finger", "metallic reflection on chest"]
            indirect_scores = [scores.get(label, 0.0) for label in indirect_labels]
            
            # Cluster-Bündelung: max(direkt, indirekt) mit Sigmoid-Dämpfung
            all_scores = direct_scores + [s * 0.001 for s in indirect_scores]  # Indirekte Scores für Sigmoid stark dämpfen
            max_positive = max(all_scores) if all_scores else 0.0
            
            # Debug-Logging für Cluster-Bündelung
            max_direct = max(direct_scores) if direct_scores else 0.0
            max_indirect = max(indirect_scores) if indirect_scores else 0.0
            logger.info(f"JEWELRY DEBUG {cluster_name}: Direct={max_direct:.4f}, Indirect={max_indirect:.4f}, Winner={max_positive:.4f}")
            
            # Gold-Boost V2: Wenn das beste direkte Label gold enthält, halbiere den noise_floor für die Berechnung
            best_label = None
            if max_direct > 0:  # Nur direkte Scores für Gold-Boost betrachten
                # Finde das beste direkte Label
                best_direct_score = 0
                best_direct_label = None
                for label in config["positive"]:
                    score = scores.get(label, 0.0)
                    if score > best_direct_score:
                        best_direct_score = score
                        best_direct_label = label
                best_label = best_direct_label
                logger.info(f"Gold-Boost DEBUG: Bestes direktes Label='{best_label}' (Score: {best_direct_score:.4f})")
            
            is_gold = best_label and "gold" in best_label.lower()
            logger.info(f"Gold-Boost DEBUG: is_gold={is_gold} für Label '{best_label}'")
            effective_noise_floor = noise_floor / 2.0 if is_gold else noise_floor
            
            # Muster-Schutz pro Cluster: Wenn has_complex_pattern aktiv ist, erhöhe DOMINANCE für Schmuck auf 2.2
            if has_complex_pattern:
                effective_noise_floor = max(effective_noise_floor, max_pattern_score * 2.2)
                logger.info(f"Komplex-Muster-Schutz: Has Complex Pattern=True, Noise Floor auf {effective_noise_floor:.4f} erhöht (Pattern: {max_pattern_score:.4f})")
            elif has_pattern:
                effective_noise_floor = max(effective_noise_floor, max_pattern_score * 2.0)
                logger.info(f"Muster-Schutz aktiv: Has Pattern=True, Noise Floor auf {effective_noise_floor:.4f} erhöht (Pattern: {max_pattern_score:.4f})")
            
            # Matte-Guard pro Cluster: Wenn matte Materialien stärker sind als metallischer Glanz, REJECT
            logger.info(f"Matte-Guard: Max Matte Score = {max_matte_score:.4f} (Schwelle: 0.03)")
            if max_matte_score > 0.03:  # Noch höhere Schwelle - nur bei echten starken Matte-Materialien
                # SNR-Logik: Matte vs. Metall
                # Finde den stärksten metallischen Score
                metallic_labels = ["gold bracelet", "silver bracelet", "gold ring", "silver ring", "gold necklace", "silver necklace"]
                max_metallic_score = max([scores.get(label, 0.0) for label in metallic_labels])
                
                # DEBUG: Metallische Scores
                logger.info(f"Matte-Guard DEBUG: Metall Scores - {[f'{label}: {scores.get(label, 0.0):.4f}' for label in metallic_labels]}")
                logger.info(f"Matte-Guard DEBUG: Max Metall Score = {max_metallic_score:.4f}")
                
                # SNR-Berechnung: Metall vs. Matte
                snr_metal_vs_matte = max_metallic_score - max_matte_score
                
                if snr_metal_vs_matte < 3.0:  # Extrem hohe Hürde für metallische Erkennung
                    effective_noise_floor = max(effective_noise_floor, max_matte_score * 3.0)
                    logger.info(f"Matte-Guard: Matte={max_matte_score:.4f} > Metall={max_metallic_score:.4f}, SNR={snr_metal_vs_matte:.4f} < 3.0 -> REJECT")
                    logger.info(f"Matte-Guard: Noise Floor auf {effective_noise_floor:.4f} erhöht (Matte-Dominanz)")
                else:
                    logger.info(f"Matte-Guard: Metall={max_metallic_score:.4f} > Matte={max_matte_score:.4f}, SNR={snr_metal_vs_matte:.4f} >= 3.0 -> ALLOW")
            else:
                logger.info(f"Matte-Guard: Keine Matte-Materialien gefunden ({max_matte_score:.4f} <= 0.03) -> DEAKTIVIERT")
            
            # Scarf-Guard pro Cluster: Kontext-abhängige Logik
            has_scarf = context.get("has_scarf", False)
            if has_scarf:
                # Wenn ein Schal da ist, erhöhe den noise_floor drastisch (Faktor 2.5)
                effective_noise_floor = max(effective_noise_floor, max_scarf_score * 2.5)
                logger.info(f"Scarf-Guard aktiv: Has Scarf=True, Noise Floor auf {effective_noise_floor:.4f} erhöht (Scarf: {max_scarf_score:.4f})")
            elif max_scarf_score > 0.015:  # Alte Logik als Fallback
                effective_noise_floor = max(effective_noise_floor, max_scarf_score * 1.5)
                logger.info(f"Scarf-Guard fallback: Noise Floor auf {effective_noise_floor:.4f} erhöht (Scarf: {max_scarf_score:.4f})")
            
            # HINWEIS-Sperre bei Schals: Wenn Schal-Guard aktiv ist, muss Schmuck SICHER sein
            scarf_guard_active = has_scarf or max_scarf_score > 0.015
            
            # Muster-Blockade (Oma-Fix): Direkte CLIP-Abfrage auf Textil-Muster
            pattern_confuser = ["plaid pattern", "fabric lines", "textile weave"]
            max_pattern_score = max([scores.get(label, 0.0) for label in pattern_confuser])
            pattern_blockade_active = max_pattern_score > 0.02
            
            # Archaeologist-Thresholds (Diamond V4 - Elena-Status-Promotion) + Schal-Schutz + Gold-Boost V2 + Sigmoid-Skalierung
            effective_threshold = 0.0030 + effective_noise_floor  # Basis-Threshold + effektiver Noise-Floor (perfekte finale Balance)
            
            if max_positive > effective_threshold:
                status = "SICHER"
            elif max_positive > (0.004 + effective_noise_floor):  # 3x höher für Sigmoid
                status = "WAHRSCHEINLICH"
            elif max_positive > (0.002 + effective_noise_floor):  # 4x höher für Sigmoid
                # Muster-Blockade (Oma-Fix): Wenn Textil-Muster stark, komplett blockieren
                if pattern_blockade_active:
                    status = "REJECTED"  # Muster-Blockade blockiert alles
                    logger.info(f"🧣 Pattern-Blockade aktiv: Textil-Muster ({max_pattern_score:.4f}) blockiert Schmuck ({max_positive:.4f})")
                elif scarf_guard_active:
                    status = "REJECTED"  # HINWEIS bei Schal komplett blockieren
                    logger.info(f"🧣 Scarf-Guard blockt HINWEIS bei Schal-Muster (Score: {max_positive:.4f})")
                else:
                    # Status-Upgrade für markante Gold-Cluster mit Gold-Boost V2
                    if any(gold_label in config["positive"] and gold_label in ["large gold hoop earrings", "multiple gold chains", "big golden hoops", "shining gold jewelry"] 
                           for gold_label in config["positive"] if scores.get(gold_label, 0.0) == max_positive):
                        status = "WAHRSCHEINLICH"  # Upgrade für Elena's markante Stücke
                    else:
                        status = "HINWEIS"
            else:
                status = "REJECTED"
                logger.debug(f"JEWELRY REJECTED: {cluster_name} (Score: {max_positive:.4f})")
            
            # Gold-Boost V2 Logging
            if is_gold:
                logger.info(f"✨ Gold-Boost V2 aktiv: Noise-Floor halbiert ({effective_noise_floor:.4f} statt {noise_floor:.4f})")
            if pattern_blockade_active:
                logger.info(f"🧣 Pattern-Blockade aktiv: Textil-Muster ({max_pattern_score:.4f}) > 0.02")
            
            # Bestes Label finden (NameError-Fix)
            if max_positive > 0:
                # Korrekte Logik: positive_scores Liste definieren
                pos_labels = config["positive"]
                pos_scores = [scores.get(l, 0.0) for l in pos_labels]  # Liste definieren!
                max_positive = max(pos_scores)
                best_label_idx = pos_scores.index(max_positive)
                best_label = pos_labels[best_label_idx]
                
                if status != "REJECTED":
                    # Kategorie-Mapping je nach Cluster-Typ
                    category_map = {
                        "bracelet": "ARMBAND",
                        "ring": "RING", 
                        "brooch": "BROSCH"
                    }
                    
                    # Spezielle Kategorisierung für Perlenketten
                    if best_label == "pearl necklace":
                        category = "SILBERNE ANHÄNGER"  # Speziell für Cluster4-2
                        logger.info(f"🛠️ PEARL-NECKLACE-MAPPING: '{best_label}' -> 'SILBERNE ANHÄNGER'")
                    else:
                        category = category_map.get(cluster_name, "SCHMUCK")
                    
                    results.append(FeatureResult(category, best_label, status, max_positive))
                    logger.info(f"PLUGIN Jewelry: {best_label} ({category}, {status}, Score: {max_positive:.4f})")
        
        return results
