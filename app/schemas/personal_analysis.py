from pydantic import BaseModel


class PersonalAnalysis(BaseModel):
    personal_analysis_id: int
    article_id: int
