from pydantic import BaseModel, Field, ConfigDict

class HistoryBase(BaseModel):
    news_id: int = Field(..., alias="newsId", description="新闻ID")