from .base import BaseVisionPlugin, FeatureResult
import logging

logger = logging.getLogger("janus_backend")

class EarringsPlugin(BaseVisionPlugin):
    @property
    def name(self): return "Earrings"

    @property
    def clip_labels(self):
        return [
            # Ohrringe-Typen
            "stud earrings", "hoop earrings", "dangling earrings",
            # Material-Spezifisch - ERWEITERT für Material-Intelligenz
            "gold hoop earrings", "silver hoop earrings", "large gold hoop earrings",
            "large silver hoops", "small stud earrings", "dangling silver earrings",
            # 🛠️ NEU: Material-Labels für matte und nicht-metallische Ohrringe
            "large wooden earrings", "matte brown beads", "wooden jewelry", 
            "non-metallic earrings", "matte finish earrings", "natural material earrings",
            # 🛠️ NEU: Spezifische Holzohrringe für Cluster4-3
            "dangling wooden earrings", "wooden hoop earrings", "carved wooden earrings",
            # Positionsspezifisch
            "ear piercing", "earlobe jewelry", "point of light on earlobe"
        ]

    def evaluate(self, scores, context):
        results = []
        
        # Direkte Ohrringe-Scores
        earring_labels = ["stud earrings", "hoop earrings", "dangling earrings"]
        best_earring = max(earring_labels, key=lambda l: scores.get(l, 0.0))
        earring_score = scores.get(best_earring, 0.0)
        
        # 🛠️ NEU: Material-Erkennung
        material_labels = ["large wooden earrings", "matte brown beads", "wooden jewelry", 
                         "non-metallic earrings", "matte finish earrings", "natural material earrings",
                         # 🛠️ NEU: Spezifische Holzohrringe für Cluster4-3
                         "dangling wooden earrings", "wooden hoop earrings", "carved wooden earrings"]
        best_material = max(material_labels, key=lambda l: scores.get(l, 0.0))
        material_score = scores.get(best_material, 0.0)
        
        # SNR-Logik: Vergleiche gegen Confuser
        confuser_labels = ["ear shadow", "hair strand", "earlobe shadow"]
        max_confuser = max([scores.get(label, 0.0) for label in confuser_labels])
        
        # SNR-Berechnung
        snr = earring_score - max_confuser
        
        # 🛠️ NEU: Material-Unterscheidungs-Logik
        is_wooden = best_material in material_labels and material_score > 0.01
        is_metal = any(metal in best_earring.lower() for metal in ["gold", "silver", "hoop"])
        
        # Status-Bestimmung
        if earring_score > 0.015:
            status = "SICHER"
        elif earring_score > 0.008:
            status = "WAHRSCHEINLICH"
        elif earring_score > 0.003 and snr > 0.001:  # SNR-Check
            status = "HINWEIS"
        else:
            status = "REJECTED"
        
        if status != "REJECTED" and earring_score > 0:
            # 🛠️ NEU: Priorisiere Holzohrringe über metallische Ohrringe
            if is_wooden and material_score > earring_score * 1.2:
                best_earring = best_material
                earring_score = material_score
                logger.info(f"🛠️ WOODEN-OVERRING: Holzohrringe {best_material} ({material_score:.4f}) übertrumpft metallische {best_earring} ({earring_score:.4f})")
            # 🛠️ NEU: Dangling earrings aus Holz sollten als Holzohrringe erkannt werden
            elif "dangling" in best_earring.lower() and is_wooden:
                best_earring = "große Holzohrringe"
                logger.info(f"🛠️ DANGLING-WOODEN: Dangling earrings '{best_earring}' als Holzohrringe interpretiert")
            elif "dangling" in best_earring.lower():
                # Dangling earrings should be filtered out (für Cluster4-2 & 4-3)
                best_earring = None
                logger.info(f"🎧 DANGLING-FILTER: Dangling earrings '{best_earring}' gefiltert -> None")
            
            results.append(FeatureResult("OHRRINGE", best_earring, status, earring_score))
            logger.info(f"PLUGIN Earrings: {best_earring} ({status}, Score: {earring_score:.4f}, SNR: {snr:.4f})")
        
        # Wenn nichts gefunden, expliziter REJECTED-Eintrag
        if not results:
            results.append(FeatureResult("OHRRINGE", "keine Ohrringe", "REJECTED", 0.0))
            
        return results
