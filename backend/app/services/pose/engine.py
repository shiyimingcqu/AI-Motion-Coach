from abc import ABC, abstractmethod


class PoseEngine(ABC):
    @abstractmethod
    def infer(self, frame):
        """Return normalized keypoints for one frame."""
