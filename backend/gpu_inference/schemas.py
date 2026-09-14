from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    sensor_context: str = Field(max_length=20000)


class GenerateResponse(BaseModel):
    answer: str
    model: str
