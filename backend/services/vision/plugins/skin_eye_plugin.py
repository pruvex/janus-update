from .base import BaseVisionPlugin, FeatureResult

class SkinEyePlugin(BaseVisionPlugin):
    @property
    def name(self): return "SkinEye"

    @property
    def clip_labels(self):
        return ["fair skin", "olive skin", "dark skin", "blue eyes", "brown eyes", "green eyes", 
                "dark eyes", "deep brown eyes", "black eyes",
                "sky reflection in eyes", "green light reflection", "window reflection in pupil"]  # Reflexions-Labels

    def evaluate(self, scores, context):
        results = []
        # Teint
        skins = [l for l in self.clip_labels if "skin" in l]
        best_skin = max(skins, key=lambda l: scores.get(l, 0.0))
        results.append(FeatureResult("TEINT", best_skin, "WAHRSCHEINLICH", scores.get(best_skin)))
        
        # Augen (sehr unsicher meistens)
        eyes = [l for l in self.clip_labels if "eyes" in l]
        best_eye = max(eyes, key=lambda l: scores.get(l, 0.0))
        eye_score = scores.get(best_eye, 0.0)
        
        # MELANIN-KORREKTUR (Cluster 2 Fix)
        # Hole Kontext-Informationen
        is_dark_hair = context.get("is_dark_hair", False)
        hair_color = context.get("hair_color", "")
        skin_tone = "fair"  # Default
        
        # Prüfe Hauttyp aus eigenem Teint-Result
        if best_skin in ["olive skin", "dark skin"]:
            skin_tone = "dark"
        
        # REFLEXIONS-BEWEIS (Cluster 2 Fix): Grüne Augen durch Reflexionen filtern
        if best_eye == "green eyes":
            # REDHEAD-SCHUTZ: Rothaarige behalten ihre grünen Augen!
            is_redhead = hair_color in ["rotbraunen", "kupferfarbenen", "roten", "rotblonden", "auburn hair"]
            
            if is_redhead:
                print(f"REDHEAD-SCHUTZ PLUGIN: Grüne Augen bei Rothaarigen geschützt - KEIN Filter!")
                # Kein Filter - behalte grüne Augen
            else:
                # Check if light-haired person (less aggressive filtering)
                is_light_hair = hair_color in ["blonde hair", "honey blonde hair", "golden blonde hair", "platinum blonde hair"]
                
                # Normaler Filter für Nicht-Rothaarige
                # Prüfe Reflexions-Scores
                reflection_labels = ["sky reflection in eyes", "green light reflection", "window reflection in pupil"]
                reflection_score = max([scores.get(label, 0.0) for label in reflection_labels])
                
                print(f"REFLEXIONS-BEWEIS: green={eye_score:.4f}, reflection={reflection_score:.4f}")
                
                # Light-haired people get more lenient treatment
                if is_light_hair:
                    # Less aggressive filtering for light-haired people
                    if eye_score < 0.02 or eye_score < reflection_score * 1.5:
                        # Grüne Augen sind wahrscheinlich Reflexion → Fallback auf braun
                        dark_eye_scores = [scores.get("brown eyes", 0.0), 
                                             scores.get("dark eyes", 0.0), 
                                             scores.get("deep brown eyes", 0.0), 
                                             scores.get("black eyes", 0.0)]
                        max_dark_score = max(dark_eye_scores)
                        
                        if max_dark_score > 0.01:
                            best_eye = "brown eyes" if max_dark_score == scores.get("brown eyes", 0.0) + 0.0001 else "dark eyes"
                            eye_score = max_dark_score
                            print(f"REFLEXIONS-FILTER (LIGHT): {best_eye} ({eye_score:.4f}) statt green eyes (Reflexion erkannt)")
                        else:
                            # Keep green eyes for light-haired people if no good dark alternative
                            print(f"LIGHT-HAIR PROTECTION: Grüne Augen behalten (keine gute Alternative)")
                    else:
                        print(f"LIGHT-HAIR PROTECTION: Grüne Augen behalten (starkes Signal)")
                else:
                    # Standard filter for others
                    if eye_score < 0.04 or eye_score < reflection_score * 5.0:
                        # Grüne Augen sind wahrscheinlich Reflexion → Fallback auf braun
                        dark_eye_scores = [scores.get("brown eyes", 0.0), 
                                             scores.get("dark eyes", 0.0), 
                                             scores.get("deep brown eyes", 0.0), 
                                             scores.get("black eyes", 0.0)]
                        max_dark_score = max(dark_eye_scores)
                        
                        if max_dark_score > 0.01:
                            best_eye = "brown eyes" if max_dark_score == scores.get("brown eyes", 0.0) + 0.0001 else "dark eyes"
                            eye_score = max_dark_score
                            print(f"REFLEXIONS-FILTER: {best_eye} ({eye_score:.4f}) statt green eyes (Reflexion erkannt)")
                        else:
                            # Keine braunen Augen gefunden → Forced Fallback auf braun bei dunklem Typ
                            if is_dark_hair and skin_tone == "dark":
                                best_eye = "brown eyes"
                                eye_score = 0.08
                                print(f"FORCED-FALLBACK: brown eyes ({eye_score:.4f}) bei dunklem Typ (keine braunen Augen gefunden)")
        
        # Doppel-Bedingung: Grüne Augen benötigen überwältigende Beweise
        if best_eye == "green eyes":
            # Prüfe die Scores aller dunklen Augenfarben
            dark_eye_scores = [scores.get("dark eyes", 0.0), 
                                 scores.get("deep brown eyes", 0.0), 
                                 scores.get("black eyes", 0.0)]
            max_dark_score = max(dark_eye_scores)
            
            print(f"DOPPEL-BEDINGUNG: green={eye_score:.4f}, max_dark={max_dark_score:.4f}, is_dark_hair={is_dark_hair}, skin_tone={skin_tone}")
            
            # BEDINGUNG 1: Grüne Augen müssen signifikant besser sein als dunkle Augen
            if max_dark_score > 0.05 and eye_score < max_dark_score * 1.5:
                best_eye = "dark eyes" if max_dark_score == scores.get("dark eyes", 0.0) + 0.0001 else "deep brown eyes"
                eye_score = max_dark_score
                print(f"DOPPEL-BEDINGUNG ERFÜLLT: {best_eye} ({eye_score:.4f}) übertrumpft green eyes ({eye_score:.4f})")
            # BEDINGUNG 2: Bei dunklem Typ + dunkler Haut sind grüne Augen unplausibel
            elif is_dark_hair and skin_tone == "dark" and max_dark_score > 0.03:
                best_eye = "brown eyes"  # Forced Fallback auf braun
                eye_score = max_dark_score + 0.01  # Bonus für Realismus
                print(f"KONTEXT-ZWANG: brown eyes ({eye_score:.4f}) bei dunklem Typ + dunkler Haut (grüne Augen unplausibel)")
            # BEDINGUNG 3: Grüne Augen brauchen Mindest-Score bei dunklem Typ
            elif is_dark_hair and eye_score < 0.12:
                best_eye = "brown eyes"  # Forced Fallback auf braun
                eye_score = 0.12  # Mindest-Score für Realismus
                print(f"MINDEST-SCORE: brown eyes ({eye_score:.4f}) bei dunklem Typ (grüne Augen Score zu niedrig)")
        # Melanin-Logik: Wenn dunkle Haare UND dunkle Haut → booste braune Augen
        elif is_dark_hair and skin_tone == "dark" and best_eye == "green eyes":
            # Bonus für braune Augen bei dunklem Typ
            brown_score = max([scores.get("brown eyes", 0.0), 
                             scores.get("dark eyes", 0.0), 
                             scores.get("deep brown eyes", 0.0), 
                             scores.get("black eyes", 0.0)])
            brown_score += 0.05  # Melanin-Bonus
            
            if brown_score > eye_score:
                best_eye = "brown eyes" if brown_score == scores.get("brown eyes", 0.0) + 0.0001 else "dark eyes"
                eye_score = brown_score
                print(f"MELANIN-KORREKTUR: {best_eye} ({eye_score:.4f}) über green eyes ({scores.get('green eyes', 0.0):.4f})")
        
        status = "SICHER" if eye_score > 0.8 else "WAHRSCHEINLICH"
        results.append(FeatureResult("AUGEN", best_eye, status, eye_score))
        
        return results
