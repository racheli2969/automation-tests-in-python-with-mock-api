from typing import Optional, Annotated
from pydantic import BaseModel, Field

class ApplicationCreate(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    description: Optional[str] = Field(None, max_length=256)

class Application(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    version: int
    etag: str
    created_at: str