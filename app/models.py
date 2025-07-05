from pydantic import BaseModel
from typing import Optional

class SentimentInput(BaseModel):
    id: Optional[str] = None
    topic_name: Optional[str] = None
    type: str
    topic_id: Optional[str] = None
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    is_kol: Optional[bool] = False
    total_interactions: Optional[int] = None