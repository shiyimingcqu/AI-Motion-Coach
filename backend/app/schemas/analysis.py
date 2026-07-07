try:
    from pydantic import BaseModel
except ModuleNotFoundError:
    BaseModel = object


class AnalysisTaskCreate(BaseModel):
    exercise: str
    source_uri: str
    camera_view: str = "front"


class SessionCreate(BaseModel):
    exercise: str
    duration_seconds: int
    total_count: int
    valid_count: int
    error_count: int
    average_score: int
