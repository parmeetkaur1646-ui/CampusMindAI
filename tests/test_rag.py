import pytest
from backend.rag_engine import CampusMindRAG
from backend.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

def test_intent_classification():
    assert CampusMindRAG.classify_intent("Where can I find my BCA syllabus?") == "syllabus"
    assert CampusMindRAG.classify_intent("What are the central library timings?") == "library"
    assert CampusMindRAG.classify_intent("What is the highest placement package at CGC Landran?") == "placements"
    assert CampusMindRAG.classify_intent("What is the eligibility for B.Tech CSE?") == "admissions"
    assert CampusMindRAG.classify_intent("What are the MST exam passing marks?") == "exam"
    assert CampusMindRAG.classify_intent("Show me my private internal attendance marks") == "escalation"

def test_context_entity_extraction():
    entities = CampusMindRAG.extract_context_entities("I want the BCA syllabus for semester 5 PHP")
    assert entities["course"] == "BCA"
    assert entities["semester"] == "5"
    assert entities["subject"] == "PHP"

def test_context_inheritance():
    # Previous context has course=BCA
    prev = {"course": "BCA", "semester": None, "subject": None}
    
    # User says "What about semester 5?"
    updated = CampusMindRAG.extract_context_entities("What about semester 5?", prev)
    assert updated["course"] == "BCA"
    assert updated["semester"] == "5"

def test_retrieval():
    docs = CampusMindRAG.retrieve_documents("library timings and books", "library_resources")
    assert len(docs) > 0
    assert any("library" in d["category"] for d in docs)
