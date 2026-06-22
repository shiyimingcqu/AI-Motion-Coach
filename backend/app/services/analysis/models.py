from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class NormalizedKeypoint:
    x: float
    y: float
    visibility: float = 1.0

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class AnalysisResult:
    exercise: str
    stage: str
    count: int = 0
    valid_count: int = 0
    score: int = 100
    errors: list[str] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
