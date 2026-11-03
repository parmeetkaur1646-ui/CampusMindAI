"""Tests for the keyword question engine and the editable data files. Run with:  python -m pytest -q"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.chat_engine import load

client = TestClient(app)


def ask(message, session_id=None):
    return client.post("/api/chat", json={"message": message, "session_id": session_id}).json()


# ---------- different questions -> different answers, same meaning -> same answer
LIBRARY = {
    "library_location": ["Where is the library?", "Library location?", "Can you tell me where the library is?", "Where can I find the library?"],
    "library_timing": ["What are the library timings?", "Library hours?"],
    "library_open_now": ["Is the library open?"],
    "library_rules": ["What are the library rules?"],
    "library_issue": ["How do I issue a book?"],
    "library_return": ["How do I return a book?"],
    "library_limit": ["How many books can I issue?"],
    "library_facilities": ["What facilities does the library have?"],
    "library_search": ["How can I search for a book?"],
    "library_digital": ["Is there a digital library?"],
    "library_contact": ["library contact and help information"],
}


@pytest.mark.parametrize("intent,questions", LIBRARY.items())
def test_library_questions_get_the_right_intent(intent, questions):
    for q in questions:
        assert ask(q)["intent"] == intent, q


def test_library_answers_are_all_different():
    answers = {ask(q[0])["message"] for q in LIBRARY.values()}
    assert len(answers) == len(LIBRARY)


def test_missing_information_is_stated_not_invented():
    assert "Information not available yet" in ask("Where is the library?")["message"]
    assert "Information not available yet" in ask("Which clubs are there?")["message"]


# ---------- academic
def test_bca_semester_5_subjects_and_other_courses():
    assert "Cloud Computing" in ask("What are BCA 5th semester subjects?")["message"]
    assert "Cloud Computing" not in ask("Show B.Tech semester 5 subjects")["message"]   # courses stay separate
    assert "not available yet" in ask("Show MCA semester 1 subjects")["message"]


def test_syllabus_notes_questions_quiz_for_a_subject():
    s = ask("PHP syllabus")["message"]; assert "Unit III" in s and "PDO" in s
    assert "Prepared statement" in ask("php notes")["message"]
    assert "Unit II" in ask("php important questions")["message"]
    d = ask("php quiz"); assert "8 multiple-choice" in d["message"] and d["actions"][0]["view"] == "quiz"


def test_incomplete_questions_ask_for_the_missing_detail():
    d = ask("Give me BCA notes.")
    assert d["intent"] == "academic_clarify" and "semester" in d["message"].lower() and "Semester 6" in d["follow_up_suggestions"]
    assert "Semester 7" not in d["follow_up_suggestions"]                       # BCA only has 6 semesters
    d = ask("5th semester", d["session_id"]); assert "Which subject" in d["message"]
    d = ask("Programming in PHP / Python", d["session_id"]); assert "Prepared statement" in d["message"]   # remembers it wanted notes


def test_course_is_asked_when_missing_and_semester_count_differs():
    d = ask("I need MBA notes"); assert "Semester 4" in d["follow_up_suggestions"] and "Semester 5" not in d["follow_up_suggestions"]
    d = ask("Give me notes"); assert "Which course" in d["message"] and "B.Tech" in d["follow_up_suggestions"]
    d = ask("B.Tech", d["session_id"]); assert "Semester 8" in d["follow_up_suggestions"]
    d = ask("Semester 9", d["session_id"]); assert "semesters 1 to 8" in d["message"]


def test_unknown_course_is_not_guessed():
    d = ask("Give me B.Pharm notes"); assert d["intent"] == "academic_unavailable" and "don't have" in d["message"]


def test_changing_course_forgets_old_semester():
    d = ask("BCA 5th semester notes"); d = ask("Give me BBA notes", d["session_id"])
    assert "Which semester" in d["message"]


# ---------- other sections and fallback
def test_ptu_cgc_and_old_features_still_work():
    assert ask("PTU examination information")["intent"] == "ptu_examination"
    assert ask("What is PTU?")["intent"] == "ptu_about"
    assert ask("Tell me about CGC Landran")["intent"] == "cgc_about"
    assert ask("What courses are available?")["intent"] == "programs"
    assert ask("btech fees")["intent"] == "fees"
    assert ask("Show me my private internal attendance marks")["intent"] == "escalation"


def test_unknown_question_gets_the_friendly_fallback():
    m = ask("zzz qqq")["message"]
    assert m.startswith("Sorry, I couldn't understand that question.") and "Quizzes" in m


# ---------- the data files (catches mistakes when you edit the JSON)
def test_academic_data_structure_is_valid():
    for course, info in load("academic")["courses"].items():
        assert info["semesters"], course
        for sem, data in info["semesters"].items():
            assert sem.isdigit() and isinstance(data["subjects"], list)
            for s in data["subjects"]:
                assert s["name"] and all(isinstance(s[k], list) for k in ("syllabus", "notes", "important_questions", "quiz")), (course, sem, s["name"])
                for q in s["quiz"]:
                    assert len(q["options"]) == 4 and q["answer"] in (0, 1, 2, 3) and q["question"], (course, s["name"], q)


def test_topic_files_are_valid():
    for name in ("library", "ptu", "cgc_landran"):
        ids = [t["id"] for t in load(name)["topics"]]
        assert len(ids) == len(set(ids)), f"duplicate topic id in {name}"
        for t in load(name)["topics"]:
            assert t["title"] and t["keywords"], (name, t["id"])


def test_bba_and_mba_data_do_not_get_mixed_up():
    bba = load("academic")["courses"]["BBA"]["semesters"]["2"]["note"]
    mba = load("academic")["courses"]["MBA"]["semesters"]["2"]["note"]
    assert "Bachelor of Business Administration" in bba and "Master of Business Administration" not in bba
    assert "Master of Business Administration" in mba and "Bachelor of Business Administration" not in mba
