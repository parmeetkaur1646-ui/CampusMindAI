"""Tests for fees / eligibility / duration (data/course_info.json) and the honest verification labels."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.chat_engine import load

client = TestClient(app)


def ask(message, session_id=None):
    return client.post("/api/chat", json={"message": message, "session_id": session_id}).json()


def test_fee_eligibility_duration_come_from_the_data_file_and_are_labelled():
    d = ask("bca fees")
    assert "Approx Rs 3.06 Lakh" in d["message"] and "confirm" in d["message"].lower() and d["verification"] == "unconfirmed"
    assert "10+2 with minimum 50%" in ask("BBA eligibility")["message"]
    assert "2 Years" in ask("mba duration")["message"]


def test_different_courses_get_different_fees():
    assert ask("msc biotech fees")["message"] != ask("biotech fees")["message"]
    assert "Rs 1.3 to 1.84 Lakh" in ask("msc biotech fees")["message"]
    assert "Rs 5.04 to 6.72 Lakh" in ask("btech cse fees")["message"]


def test_follow_up_uses_the_last_course():
    d = ask("bca fees"); d = ask("eligibility?", d["session_id"])
    assert "BCA: eligibility" in d["message"]


def test_course_is_asked_when_missing():
    d = ask("fees"); assert d["intent"] == "course_clarify" and "BCA" in d["follow_up_suggestions"]
    assert "Fee:" in ask("BBA", d["session_id"])["message"]


def test_courses_not_in_the_data_are_not_invented():
    d = ask("mca fees"); assert d["verification"] == "none" and "won't guess" in d["message"] and "Lakh" not in d["message"]


def test_hostel_fee_question_goes_to_hostel_topic():
    d = ask("hostel fees"); assert d["intent"] == "cgc_hostel" and "1.40 Lakh" in d["message"]


def test_badge_is_not_verified_when_answer_says_it_could_not_find():
    assert ask("mca fees")["verification"] != "verified"
    assert ask("How many books can I issue?")["verification"] == "unconfirmed"     # official rule plus one unconfirmed extra
    assert ask("What are the library rules?")["verification"] == "verified"
    assert ask("Where is the library?")["verification"] == "none"                 # location still says "not available yet"
    assert ask("zzz qqq")["verification"] == "none"


def test_cpp_subject_is_matched_and_lists_are_one_item_per_line():
    d = ask("Object Oriented Programming using C++ syllabus")
    assert "Semester 2" in d["message"] and "C++" in d["message"]
    assert "\n- Toll-free" in ask("mca fees")["message"]       # markdown list, not bullets glued on one line


def test_faculty_and_library_data_from_the_help_desk_code():
    assert "Dr. Inderpreet Kaur" in ask("Who is the HOD of computer applications?")["message"]
    m = ask("How many books can I issue?")["message"]
    assert "3 books for 21 days" in m and "14 days" not in m and "meritorious" in m   # official rule; the extra claim is flagged


def test_course_info_file_is_valid():
    for key, c in load("course_info")["courses"].items():
        assert all(c[k] for k in ("name", "duration", "eligibility", "fee", "aliases")), key
