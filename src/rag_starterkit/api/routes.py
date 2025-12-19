from fastapi import APIRouter
from rag_starterkit.api.schemas import IngestRequest, QueryRequest, QueryResponse
from rag_starterkit.data.ingest import ingest_folder
from rag_starterkit.rag.retriever import retrieve_context
from rag_starterkit.rag.generator import generate_answer

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/v1/ingest")
def ingest(req: IngestRequest):
    result = ingest_folder(req.path)
    return {"ingested": result}

@router.post("/v1/query", response_model=QueryResponse)
def query(req: QueryRequest):
    contexts = retrieve_context(req.query, top_k=req.top_k)
    answer, citations = generate_answer(req.query, contexts)
    return QueryResponse(answer=answer, citations=citations)
