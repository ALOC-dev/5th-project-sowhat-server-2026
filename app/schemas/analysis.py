from pydantic import BaseModel

class ArticleAnalysis(BaseModel):
    summary: str
    impact: str
    action: str