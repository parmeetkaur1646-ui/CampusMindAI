import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.official_answers import match_programs

client = TestClient(app)


def ask(msg, sid=None):
    return client.post("/api/chat", json={"message": msg, "session_id": sid}).json()


def test_different_questions_get_different_answers():
    qs = ["btech fees", "mca fees", "library rules", "mca placements", "how to apply", "contact number", "blah blah xyz"]
    answers = {ask(q)["message"] for q in qs}
    assert len(answers) == len(qs)


def test_fees_never_invent_numbers_and_name_the_programme():
    m = ask("mca fees")["message"]
    assert "MCA" in m and "won't guess" in m and "₹" not in m and "Rs" not in m
    assert "1800-200-3575" in m


def test_unknown_question_is_honest_not_generic_highlights():
    d = ask("blah blah xyz")
    assert d["intent"] == "unknown" and "Highlights" not in d["message"] and d["grounded"] is False


def test_programme_matching():
    assert match_programs("btech cse")[0]["name"] == "B.Tech Computer Science Engineering (CSE)"
    assert match_programs("cse fees")[0]["name"] == "B.Tech Computer Science Engineering (CSE)"
    assert match_programs("b.pharm")[0]["name"] == "Bachelor of Pharmacy (B.Pharm)"
    assert match_programs("mba digital marketing")[0]["name"] == "MBA (Digital Marketing)"
    assert len(match_programs("btech")) > 5


def test_syllabus_followup_keeps_context_and_works_for_other_courses():
    d = ask("I need my MBA syllabus")
    d = ask("Semester 2", d["session_id"])
    assert "MBA Semester 2" in d["message"] and any("ptu.ac.in/syllabus" in x["url"] for x in d["sources"])


def test_syllabus_endpoint_returns_official_sources_for_any_programme():
    r = client.get("/api/academic/syllabus", params={"course": "B.Pharm", "semester": "3"}).json()
    assert any("ptu.ac.in" in x["url"] for x in r["resources"]) and any("pharmacy" in x["url"] for x in r["resources"])


def test_quiz_and_notes_are_honest_without_ai_key():
    q = client.post("/api/academic/quiz", json={"subject": "DBMS"}).json()
    assert q["questions"] == [] and "AI key" in q["message"]
    assert len(client.post("/api/academic/quiz", json={"subject": "PHP", "count": 3}).json()["questions"]) == 3
