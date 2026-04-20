from abc import ABC, abstractmethod
from typing import List, Dict, Any

class FeatureResult:
    def __init__(self, category: str, label: str, status: str, score: float):
        self.category = category
        self.label = label
        self.status = status  # "SICHER", "WAHRSCHEINLICH", "UNSICHER"
        self.score = score

    def __repr__(self):
        return f"{self.category}: {self.label} ({self.status}, {self.score:.3f})"

class BaseVisionPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def clip_labels(self) -> List[str]:
        pass

    @abstractmethod
    def evaluate(self, scores: Dict[str, float], context: Dict[str, Any]) -> List[FeatureResult]:
        pass
