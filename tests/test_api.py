import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.main import app
from app.db import create_tables

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    create_tables()
    yield

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "KPGU AI University Assistant API"}

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data

def test_conversations_crud():
    # 1. Create conversation
    create_res = client.post("/api/conversations", json={"title": "Test Chat"})
    assert create_res.status_code == 200
    conv_data = create_res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Test Chat"

    # 2. Get conversation
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == conv_id

    # 3. Update title via PUT
    put_res = client.put(f"/api/conversations/{conv_id}", json={"title": "Updated Title"})
    assert put_res.status_code == 200
    assert put_res.json()["title"] == "Updated Title"

    # 4. Add message
    msg_res = client.post(f"/api/conversations/{conv_id}/messages", json={
        "role": "user",
        "content": "Hello KPGU"
    })
    assert msg_res.status_code == 200
    assert msg_res.json()["content"] == "Hello KPGU"

    # 5. List messages
    msgs_res = client.get(f"/api/conversations/{conv_id}/messages")
    assert msgs_res.status_code == 200
    assert len(msgs_res.json()) >= 1

    # 6. Delete conversation
    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200

def test_knowledge_status_endpoint():
    response = client.get("/api/knowledge/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "document_count" in data
    assert "chunk_count" in data

def test_sources_endpoint():
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upload_document_endpoint():
    response = client.post("/api/knowledge/upload", json={
        "title": "Test Admission Guide",
        "content": "KPGU offer various undergraduate and postgraduate courses in engineering, pharmacy and management.",
        "url": "https://www.kpgu.ac.in/test-admissions"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "document_id" in data
