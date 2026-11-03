"""Tests for the programme list (data/cgc_programmes.json), the Courses endpoint, and chatbot matching that uses it."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.chat_engine import load
from backend.official_answers import match_programs

client = TestClient(app)


def ask(message, session_id=None):
    return client.post("/api/chat", json={"message": message, "session_id": session_id}).json()


def test_all_programmes_are_listed_in_six_groups_with_links():
    data = client.get("/api/courses").json()
    names = [d["department"] for d in data["departments"]]
    assert names == ["Engineering - B.Tech / M.Tech", "Computer Applications", "Business and Commerce", "Pharmacy",
                     "Science and Biotechnology", "Hotel Management and Tourism"]
    programs = [p for d in data["departments"] for p in d["programs"]]
    assert len(programs) == 41
    assert all(p["cgc_url"] is None or p["cgc_url"].startswith("https://www.cgc.edu.in/") for p in programs)
    assert [p["name"] for p in programs if p["cgc_url"] is None] == ["BCA Lateral Entry (LEET)"]


def test_courses_tab_shows_batches_and_does_not_invent_details():
    progs = {p["name"]: p for d in client.get("/api/courses").json()["departments"] for p in d["programs"]}
    bca = progs["Bachelor of Computer Applications (BCA)"]
    assert bca["ptu_batches"] == "2011, 2015, 2019, 2021, 2025" and bca["approximate"] and bca["duration"] == "3 Years"
    mca = progs["Master of Computer Applications (MCA)"]
    assert mca["duration"] == "Information not available yet" and mca["approximate"] is False
    assert progs["B.Sc. Multimedia"]["ptu_batches"] is None
    assert progs["Pharm.D (Doctor of Pharmacy)"]["level"] == "Doctor of Pharmacy"


def test_department_filter():
    d = client.get("/api/courses", params={"department": "Pharmacy"}).json()
    assert d["count"] == 1 and len(d["departments"][0]["programs"]) == 8


def test_chatbot_still_matches_programmes_from_the_data_file():
    assert match_programs("btech cse")[0]["name"] == "B.Tech Computer Science Engineering (CSE)"
    assert "cgc.edu.in/mba-digital-marketing" in ask("tell me about mba digital marketing")["message"]
    assert "Programmes at CGC" in ask("What courses are available?")["message"]


def test_programme_file_is_valid():
    seen = set()
    for cat in load("cgc_programmes")["categories"]:
        for p in cat["programmes"]:
            assert p["name"] and p["level"] and p["name"] not in seen
            seen.add(p["name"])
            assert p["cgc_url"] is None or p["cgc_url"].startswith("https://")
    names = {e["name"] for e in load("ptu_syllabus_index")["programmes"]}
    for cat in load("cgc_programmes")["categories"]:
        for p in cat["programmes"]:
            assert p["ptu_index"] is None or p["ptu_index"] in names, p["name"]
