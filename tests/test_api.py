import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "CGC" in data["institution"] or "Chandigarh" in data["institution"]

def test_college_info():
    res = client.get("/api/college/info")
    assert res.status_code == 200
    data = res.json()
    assert "Landran" in data["location"]
    assert "IKGPTU" in data["affiliation"]

def test_placements():
    res = client.get("/api/college/placements")
    assert res.status_code == 200
    data = res.json()
    assert "9,000+" in data["total_offers"]
    assert "54.75 LPA" in data["highest_package"]

def test_library_resources():
    res = client.get("/api/library/resources")
    assert res.status_code == 200
    data = res.json()
    assert len(data["resources"]) > 0
    # Only resources listed on the official library page
    titles = [r["title"] for r in data["resources"]]
    assert any("Library Rules" in t for t in titles)
    assert any("Digi Library" in t for t in titles)
    assert not any("IEEE" in t or "NDLI" in t for t in titles)

def test_academic_syllabus():
    res = client.get("/api/academic/syllabus?course=BCA&semester=5")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    assert any("BCA" in doc["title"] or "BCA" in doc["content"] for doc in data["results"])

def test_department_name_query():
    res = client.post("/api/chat", json={"message": "department name"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "cgc_departments"
    assert "Department of Computer Applications" in data["message"]
    assert "Chandigarh Engineering College" in data["message"]

def test_context_aware_chat_and_memory():
    session_id = "test-session-suite-101"
    
    # 1. Ask initial question about BCA
    res1 = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Where can I find my BCA syllabus?"
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["memory"]["course"] == "BCA"
    
    # 2. Follow-up without repeating course: "What about semester 5?"
    res2 = client.post("/api/chat", json={
        "session_id": session_id,
        "message": "What about semester 5?"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    # It must retain course=BCA and understand semester=5!
    assert data2["memory"]["course"] == "BCA"
    assert data2["memory"]["semester"] == "5"
    assert "BCA" in data2["message"] or "PHP" in data2["message"] or "Cloud" in data2["message"]

def test_admin_flow():
    # 1. Login with admin credentials
    res_login = client.post("/api/admin/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    
    # 2. Fetch documents with auth token
    res_docs = client.get("/api/admin/documents", headers={"Authorization": f"Bearer {token}"})
    assert res_docs.status_code == 200
    data_docs = res_docs.json()
    assert data_docs["count"] > 0
