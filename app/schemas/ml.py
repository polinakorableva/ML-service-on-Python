from pydantic import BaseModel
from typing import Any


class PredictRequest(BaseModel):
    model_id: int
    features: list[float]


class JobResponse(BaseModel):
    id: int
    status: str
    result: Any = None

    class Config:
        from_attributes = True


class ModelResponse(BaseModel):
    id: int
    name: str
    file_path: str

    class Config:
        from_attributes = True