from pydantic import BaseModel

class CommonAnalysis(BaseModel):
    summary: str
    keyword: str