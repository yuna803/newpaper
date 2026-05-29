from pydantic import BaseModel, Field, ConfigDict

class FavoriteBase(BaseModel):
    news_id: int = Field(..., alias="newsId", description="新闻ID")