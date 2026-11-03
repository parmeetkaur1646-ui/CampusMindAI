"""Tests for the PTU syllabus information (data/ptu_syllabus_index.json, copied from ptu.ac.in/syllabus)."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.chat_engine import load, ptu_lookup

client = TestClient(app)


def ask(message, session_id=None):
    return client.post("/api/chat", json={"message": message, "session_id": session_id}).json()


def test_schemes_question_lists_published_batches():
    d = ask("Which syllabus schemes does PTU have for MCA?")
    assert d["intent"] == "ptu_syllabus_schemes" and "2003, 2012, 2015, 2019, 2020, 2021, 2025" in d["message"]
    assert d["verification"] == "verified" and d["sources"][0]["url"] == "https://ptu.ac.in/syllabus"
    assert "2011, 2015, 2019, 2021, 2025" in ask("BCA syllabus batches")["message"]


def test_syllabus_answers_show_batches_and_link_to_the_ptu_page():
    d = ask("Show me the BCA semester 2 syllabus")
    assert "2011, 2015, 2019, 2021, 2025" in d["message"] and d["sources"][0]["url"] == "https://ptu.ac.in/syllabus"
    assert "B.Tech CSE" in ask("Give me B.Tech 3rd semester syllabus")["message"]


def test_other_programmes_use_the_same_index():
    assert "2005, 2009" in ask("B.Pharm syllabus")["message"]
    assert [e["name"] for e in ptu_lookup("btech cse")] == ["B.Tech CSE"]
    assert len(ptu_lookup("mba")) == 2


def test_programme_not_on_the_ptu_page_is_not_invented():
    assert ptu_lookup("bsc biotech") == []
    assert "not found on the page" in load("ptu_syllabus_index")["not_listed"]


def test_old_ptu_link_is_gone():
    import os
    for folder in ("backend", "frontend", "data"):
        for root, _, files in os.walk(folder):
            for f in files:
                if f.endswith((".py", ".js", ".html", ".json", ".txt")):
                    assert "amritsar.ptu.ac.in" not in open(os.path.join(root, f), encoding="utf-8").read(), f


def test_official_library_rules_are_used():
    m = ask("What are the library rules?")["message"]
    assert "stamp-size photograph" in m and "21 days" in m and "property counter" in m and "Rs. 2" not in m
