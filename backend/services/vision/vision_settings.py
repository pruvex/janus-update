class VisionSettings:
    def __init__(self):
        self.vision_min_score: float = 0.001 # Zurückgesetzt auf Originalwert, um mehr Labels zu erfassen
        self.vision_enabled: bool = True
