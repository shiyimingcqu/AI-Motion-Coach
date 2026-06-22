try:
    from pydantic import BaseModel
except ModuleNotFoundError:
    BaseModel = object


class AnalysisTaskCreate(BaseModel):
    exercise: str
    source_uri: str
