from pydantic import BaseModel
from typing import List, Optional

class OrderCreate(BaseModel):
    target_link: str
    source_links: List[str]
    desired_count: int = 100

class OrderAction(BaseModel):
    type: str  # pause | resume | cancel