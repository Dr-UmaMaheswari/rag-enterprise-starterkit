from pydantic import BaseModel, Field
from typing import List

class IngestRequest(BaseModel):
    path: str = Field(..., description="Local folder path containing documents to ingest.")

class QueryRequest(BaseModel):
    query: str
    top_k: int = 4

class Citation(BaseModel):
    source_id: str
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
