from fastapi.testclient import TestClient
from rag_starterkit.main import app

client = TestClient(app)

def test_query_contract():
    r = client.post("/v1/query", json={"query": "test", "top_k": 2})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "citations" in data
