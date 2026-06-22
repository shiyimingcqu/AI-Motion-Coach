from dataclasses import dataclass


@dataclass
class User:
    id: str
    username: str
    role: str


@dataclass
class TrainingSession:
    id: str
    user_id: str
    exercise: str
    duration_seconds: int
    total_count: int
    valid_count: int
    error_count: int
    average_score: float
