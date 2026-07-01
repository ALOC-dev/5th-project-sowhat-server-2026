from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
import app.services.article as article_service
import app.services.user as user_service

from app.schemas.article import ArticlePreviewResponse, ArticleDetailResponse

router = APIRouter(prefix="/api/news", tags=["News"])

@router.get("/recommend", response_model=List[ArticlePreviewResponse])
def get_recommended_articles(
    user_id: int, 
    db: Session = Depends(get_db)
):
    recommended_list = article_service.get_recommended_articles(db, user_id)
    return recommended_list

@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article_detail(
    article_id: int, 
    user_id: int, 
    db: Session = Depends(get_db)
):
    article_analysis = await article_service.get_personal_analysis(db, article_id, user_id)
    
    try:
        user_service.update_user_interests(db, user_id, article_id)
    except Exception as e:
        print(f"Failed to update user interests: {e}")
        
    return article_analysis

