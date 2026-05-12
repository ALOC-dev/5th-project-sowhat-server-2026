from pydantic import BaseModel


class PersonalAnalysis(BaseModel):
    effect: str
    solution: str
