"""
Deterministic, keyword-based understanding engine for CampusMind AI.

Updates Included:
  - Department-wise fee structures (Engineering, Computer Applications, Management,
    Pharmacy, Science & Biotech, Hotel Management, Hostel & Additional Costs).
  - Stream-specific placement statistics & top recruiters.
  - Full departmental library portals & e-resources (CEC, CBSA, CCT, CCP, Training).
  - Primary helplines, alternate admission lines, WhatsApp support, and campus welfare officers.
  - Step-by-step PTU syllabus navigation & PTU exam portal links (https://www.ptuexam.com/).
  - Comprehensive campus infrastructure & facilities (40+ acre Mohali campus).
  - Complete course catalog covering 50+ UG/PG/LEET/Doctorate programs.
"""

import json
import os
import re
from typing import Dict, List, Optional

from backend.database import get_db_connection

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PTU_PORTAL = {"title": "PTU Syllabus Portal", "source_title": "Official", "url": "https://ptu.ac.in/syllabus"}
PTU_EXAM_PORTAL = {"title": "IKGPTU Exam Portal", "source_title": "Official", "url": "https://www.ptuexam.com/"}
NOT_AVAILABLE = "Information not available yet. Please contact the college help desk."


def load(name: str) -> dict:
    """Read a JSON data file dynamically."""
    with open(os.path.join(DATA_DIR, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def load_courses(name: str) -> list:
    """Return ONE flat list of course dicts from a data file.

    The data files (cgc_programmes.json, course_info.json, ptu_syllabus_index.json) are grouped like this:
        {"categories": [ {"category_name": "...", "courses": [ {...}, {...} ]}, ... ]}
    This function walks through every category and collects all the courses into one list.
    """
    data = load(name)
    if "categories" in data:
        courses = []
        for category in data["categories"]:
            courses += category.get("courses", category.get("programmes", []))
        return courses
    courses = data.get("courses", data.get("programmes", []))
    return list(courses.values()) if isinstance(courses, dict) else courses


# ------------------------------------------------------------------ 1. Text Cleaning
def clean(text: str) -> str:
    t = text.lower()
    t = re.sub(r"\b([bm])\.\s?(tech|sc|com|pharm)\b", r"\1\2", t)      # b.tech -> btech
    t = re.sub(r"\bb\s+tech\b", "btech", t)
    t = re.sub(r"\bc\+\+\b", "cpp", t)
    t = re.sub(r"[^a-z0-9+\s]", " ", t)                                # drop punctuation
    return re.sub(r"\s+", " ", t).strip()


def contains(text: str, keyword: str) -> bool:
    """True if keyword/phrase appears as a whole word match."""
    return re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(s|es|ed|ing)?(?![a-z0-9])", text) is not None


# ------------------------------------------------------------------ 2. Academic Intent Matching
WHAT = {
    "quiz": ["quiz", "mcq", "test me"],
    "important_questions": ["important question", "important questions", "imp questions", "expected questions", "important qs"],
    "syllabus": ["syllabus", "curriculum", "units", "scheme"],
    "notes": ["notes", "note", "study material"],
    "subjects": ["subjects", "subject list", "list of subjects", "papers", "what subjects", "which subjects"],
}
WHAT_LABEL = {
    "quiz": "quiz",
    "important_questions": "important questions",
    "syllabus": "syllabus",
    "notes": "notes",
    "subjects": "subjects",
}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8}


def find_what(t: str) -> Optional[str]:
    for what, words in WHAT.items():
        if any(contains(t, w) for w in words):
            return what
    return None


def find_semester(t: str) -> Optional[int]:
    m = re.search(r"\bsem(?:ester)?\s*(\d{1,2})\b", t) or re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s*sem(?:ester)?\b", t)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(" + "|".join(ORDINALS) + r")\s+sem", t)
    if m:
        return ORDINALS[m.group(1)]
    m = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?$", t) or re.match(r"^(" + "|".join(ORDINALS) + r")$", t)
    if m:
        return int(m.group(1)) if m.group(1).isdigit() else ORDINALS[m.group(1)]
    return None


def find_course(t: str, courses: dict) -> Optional[str]:
    best_key, best_score = None, -1
    for key, info in courses.items():
        names = [key, info.get("full_name", "")] + info.get("aliases", [])
        score = 0
        for n in names:
            if not n:
                continue
            clean_n = clean(n)
            if contains(t, clean_n):
                score = max(score, len(clean_n.split()))
        if score > 0 and (score > best_score or (score == best_score and best_key is not None and len(key) > len(best_key))):
            best_key, best_score = key, score
    return best_key


def subject_words(subject: dict) -> List[str]:
    names = [subject["name"]] + subject.get("aliases", []) + [subject.get("code") or ""]
    names += re.split(r"[/()]", subject["name"])
    return [clean(n) for n in names if len(clean(n)) >= 3]


def find_subjects(t: str, courses: dict, course: Optional[str], semester: Optional[int]) -> list:
    found = []
    for c, info in courses.items():
        if course and c != course:
            continue
        semesters = info.get("semesters", {})
        for sem, sem_data in semesters.items():
            if semester and int(sem) != semester:
                continue
            for subj in sem_data.get("subjects", []):
                if any(contains(t, w) for w in subject_words(subj)):
                    found.append((c, int(sem), subj))
    return found


# ------------------------------------------------------------------ PTU Syllabus Batches
def ptu_lookup(text: str) -> List[dict]:
    t, found, best = clean(text), [], 0
    for entry in load_courses("ptu_syllabus_index"):
        for alias in entry.get("aliases", []):
            if len(alias) < 3:          # very short words like "it" would match normal sentences
                continue
            if contains(t, clean(alias)):
                if len(alias) > best:
                    found, best = [], len(alias)
                if len(alias) == best and entry not in found:
                    found.append(entry)
    return found


def schemes_text(entries: list) -> str:
    if not entries:
        return ""
    lines = "\n".join(
        f"- **{e.get('name') or e.get('programme')}:** {e.get('batches') or 'Information not available yet'}"
        for e in entries
    )
    return (
        "\n\n**Syllabus batches published on PTU's syllabus portal (ptu.ac.in/syllabus):**\n"
        + lines
        + "\nOpen the page, choose the scheme for your admission year, and confirm with your department."
    )


def schemes_reply(text: str) -> Optional[Dict]:
    if not re.search(r"\b(schemes?|batch(es)?)\b", clean(text)):
        return None
    entries = ptu_lookup(text)
    if not entries:
        return None
    return make_reply(
        "### PTU syllabus schemes" + schemes_text(entries),
        "ptu_syllabus_schemes",
        [f"{entries[0]['name']} semester 1 subjects"],
        [PTU_PORTAL],
        verification="verified",
    )


def save_state(session_id, course, semester, subject, wanted):
    conn = get_db_connection()
    conn.execute(
        "UPDATE student_memory SET course=?, semester=?, subject=?, notes=? WHERE session_id=?",
        (course, str(semester) if semester else None, subject, wanted, session_id),
    )
    conn.commit()
    conn.close()


def make_reply(text, intent, suggestions=(), sources=(), actions=(), grounded=True, verification="none") -> Dict:
    return {
        "answer": text,
        "intent": intent,
        "follow_up_suggestions": list(suggestions),
        "sources": list(sources),
        "actions": list(actions),
        "grounded": grounded,
        "verification": verification,
    }


def open_button(label, course, semester=None, subject=None, view=None):
    return {"label": label, "course": course, "semester": semester, "subject": subject, "view": view}


# ------------------------------------------------------------------ Academic Reply Engine
def academic_reply(text: str, session_id: str, memory: dict) -> Optional[Dict]:
    t = clean(text)
    data = load("academic")["courses"]
    pending = memory.get("notes") if memory.get("notes") in WHAT else None

    course_now, sem_now, what_now = find_course(t, data), find_semester(t), find_what(t)
    mem_course = find_course(clean(memory.get("course") or ""), data)
    mem_sem = int(memory["semester"]) if str(memory.get("semester") or "").isdigit() else None

    mentions_ptu = bool(re.search(r"\b(ptu|ikgptu|gujral|university)\b", t))
    all_subject_hits = find_subjects(t, data, None, None) if (what_now or pending) else []
    subject_hits = all_subject_hits if all_subject_hits else find_subjects(t, data, course_now or mem_course, sem_now or mem_sem) if (what_now or pending) else []
    academic = (
        (what_now and (course_now or sem_now or subject_hits or not mentions_ptu))
        or (course_now and sem_now)
        or (pending and (course_now or sem_now or subject_hits))
        or (sem_now and mem_course)
    )
    if mentions_ptu and not (course_now or sem_now or subject_hits):
        academic = False
    if not academic:
        return None

    changed = bool(course_now and mem_course and course_now != mem_course)
    course = course_now or mem_course
    semester = sem_now or (None if changed else mem_sem)
    if subject_hits:
        course, semester = subject_hits[0][0], semester or subject_hits[0][1]
    wanted = what_now or pending or "subjects"
    subj_text = None if (changed or (sem_now and mem_sem and sem_now != mem_sem)) else memory.get("subject")

    if not course:
        from backend.official_answers import match_programs

        other = match_programs(text)
        if other:
            published = schemes_text(ptu_lookup(text)) if wanted == "syllabus" else ""
            return make_reply(
                f"I don't have {WHAT_LABEL[wanted]} for {other[0]['name']} in this app yet. {NOT_AVAILABLE}{published}\n\n"
                f"Courses with academic data: {', '.join(data)}.",
                "academic_unavailable",
                list(data),
                [PTU_PORTAL],
                grounded=bool(published),
            )
        save_state(session_id, None, semester, None, wanted)
        return make_reply(f"Sure. Which course do you need the {WHAT_LABEL[wanted]} for?", "academic_clarify", list(data), grounded=False)

    info = data[course]
    semesters = info.get("semesters", {})
    max_sem = len(semesters)

    if not semester or str(semester) not in semesters:
        save_state(session_id, course, None, None, wanted)
        msg = f"{course} has semesters 1 to {max_sem}. " if semester else "Sure. "
        return make_reply(
            msg + f"Which semester do you need for {course}?",
            "academic_clarify",
            [f"Semester {n}" for n in range(1, max_sem + 1)],
            grounded=False,
        )

    sem_data = semesters[str(semester)]
    subjects = sem_data.get("subjects", [])
    display_course = "B.Tech CSE" if course == "B.Tech" else course
    label = f"{display_course} Semester {semester}"
    caution = (
        "\n\n*From the project's stored data, not confirmed against the official PTU syllabus. Please verify on the PTU portal.*"
        if info.get("source") == "project_data"
        else ""
    )
    nav = [open_button(f"Open {label} in Academic", course, semester)]
    schemes = schemes_text(ptu_lookup(course)) if wanted == "syllabus" else ""

    if wanted == "subjects":
        save_state(session_id, course, semester, None, None)
        if not subjects:
            note = f"\n\n{sem_data['note']}" if sem_data.get("note") else ""
            return make_reply(
                f"### {label}: subjects\n\nThe subject list is not available yet.{note}\n\n{NOT_AVAILABLE}{caution}",
                "semester_information",
                [],
                [PTU_PORTAL],
                nav,
                grounded=False,
            )
        lines = "\n".join(f"• {s['name']}" + (f" ({s['code']})" if s.get("code") else "") for s in subjects)
        return make_reply(
            f"### {label}: subjects\n\n{lines}{caution}",
            "semester_information",
            [f"{label} notes", f"{label} syllabus", f"{label} quiz", f"{label} important questions"],
            [PTU_PORTAL],
            nav,
            verification="unconfirmed",
        )

    chosen = next((s for (_, sm, s) in subject_hits if sm == semester), None)
    if not chosen and subj_text:
        chosen = next((s for s in subjects if s["name"] == subj_text), None)
    if not chosen and len(subjects) == 1:
        chosen = subjects[0]
    if not chosen and wanted == "syllabus":
        save_state(session_id, course, semester, None, None)
        parts = []
        for s in subjects:
            units = (
                "\n".join(f"  - **{u['unit']}:** {u['topics']}" for u in s.get("syllabus", []))
                or "  - Information not available yet."
            )
            parts.append(f"**{s['name']}**\n{units}")
        body = "\n\n".join(parts) if parts else (sem_data.get("note") or "The syllabus is not available yet.") + f"\n\n{NOT_AVAILABLE}"
        if info.get("overview") and not any(sb.get("syllabus") for sb in subjects):
            body += f"\n\n{info['overview']}"
        body += schemes
        return make_reply(f"### {label}: syllabus\n\n{body}{caution}", "syllabus", [], [PTU_PORTAL], nav, grounded=bool(parts))

    if not chosen:
        if not subjects:
            save_state(session_id, course, semester, None, None)
            return make_reply(
                f"I don't have the subjects for {label} yet, so I can't show the {WHAT_LABEL[wanted]}. {NOT_AVAILABLE}",
                wanted,
                [],
                [PTU_PORTAL],
                nav,
                grounded=False,
            )
        save_state(session_id, course, semester, None, wanted)
        return make_reply(
            f"Which subject of {label} do you need the {WHAT_LABEL[wanted]} for?",
            "academic_clarify",
            [s["name"] for s in subjects],
            grounded=False,
        )

    save_state(session_id, course, semester, chosen["name"], None)
    title, go = f"{label} · {chosen['name']}", open_button(f"Open {chosen['name']} in Academic", course, semester, chosen["name"], wanted)
    more = [f"{chosen['name']} {w}" for w in ("syllabus", "notes", "important questions", "quiz") if w != WHAT_LABEL[wanted]]
    overview = f"\n\n{info['overview']}" if wanted == "syllabus" and info.get("overview") else ""

    def empty(what):
        return make_reply(
            f"### {title}\n\nI don't have the {what} for this subject yet. {NOT_AVAILABLE}{overview}{schemes}",
            wanted,
            more,
            [PTU_PORTAL],
            [go],
            grounded=False,
        )

    if wanted == "syllabus":
        if not chosen.get("syllabus"):
            return empty("syllabus")
        body = "\n".join(f"• **{u['unit']}:** {u['topics']}" for u in chosen["syllabus"])
        return make_reply(f"### {title}: syllabus\n\n{body}\n\n{chosen.get('syllabus_note', '')}{caution}{schemes}", "syllabus", more, [PTU_PORTAL], [go])

    if wanted == "notes":
        if not chosen.get("notes"):
            return empty("notes")
        blocks = []
        for n in chosen["notes"]:
            b = f"#### {n['unit']}: {n['title']}\n{n['explanation']}"
            if n.get("definitions"):
                b += "\n\n**Important definitions**\n" + "\n".join(f"• **{a}:** {d}" for a, d in n["definitions"])
            if n.get("example"):
                b += f"\n\n**Example**\n```\n{n['example']}\n```"
            if n.get("exam_points"):
                b += "\n\n**Exam points**\n" + "\n".join(f"• {p}" for p in n["exam_points"])
            blocks.append(b)
        return make_reply(
            f"### {title}: notes\n*Study notes to help revision. They are not official university material.*\n\n" + "\n\n".join(blocks),
            "notes",
            more,
            [],
            [go],
        )

    if wanted == "important_questions":
        if not chosen.get("important_questions"):
            return empty("important questions")
        body = "\n\n".join(
            f"**{g['unit']}**\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(g["questions"], 1))
            for g in chosen["important_questions"]
        )
        return make_reply(
            f"### {title}: important questions\n\n{body}\n\n*{chosen.get('questions_note', '')}*",
            "important_questions",
            more,
            [],
            [go],
        )

    if not chosen.get("quiz"):
        return empty("quiz")
    return make_reply(
        f"### {title}: quiz\n\nThere are **{len(chosen['quiz'])} multiple-choice questions**. Press the button to start; your score is shown at the end.",
        "quiz",
        more,
        [],
        [go],
    )


# ------------------------------------------------------------------ 3. Topic Sections & Keyword Scoring
def pick_topic(t: str, topics: list) -> Optional[dict]:
    best, best_score = None, 0
    for topic in topics:
        score = sum(len(k.split()) for k in topic["keywords"] if contains(t, k))
        if score > best_score:
            best, best_score = topic, score
    return best


def topic_reply(section: str, topic: dict, section_title: str) -> Dict:
    parts = []
    if topic.get("answer"):
        parts.append(topic["answer"])
    if topic.get("unconfirmed"):
        parts.append(
            "**From the project's stored data (not yet confirmed against the official website):**\n"
            + topic["unconfirmed"]
        )
    if not parts:
        parts.append(NOT_AVAILABLE)

    links = topic.get("links", []) or []
    sources = [
        {
            "title": l.get("title", "Official Source"),
            "source_title": "Official",
            "url": l.get("url", "#"),
        }
        for l in links
        if isinstance(l, dict)
    ]

    gap = "not available yet" in " ".join(parts)
    verification = (
        "unconfirmed"
        if topic.get("unconfirmed")
        else ("verified" if topic.get("answer") and not gap else "none")
    )
    
    topic_title = topic.get("title", section_title)
    topic_id = topic.get("id", "general")

    return make_reply(
        f"### {topic_title}\n\n" + "\n\n".join(parts),
        f"{section}_{topic_id}",
        topic.get("follow_ups", []),
        sources,
        grounded=bool(topic.get("answer") or topic.get("unconfirmed")),
        verification=verification,
    )


AREA_WORDS = {
    "library": r"\b(library|librarian|books?|e-?books?|journals?|magazines?|newspapers?|opac|borrow|book bank)\b",
    "ptu": r"\b(ptu|ikgptu|gujral|university|exams?|examination|results?|date ?sheet|admit card|regulations?|ordinances?|grading|cgpa|re-?appear)\b",
}


# ------------------------------------------------------------------ Course Info (Fees / Eligibility / Duration)
COURSE_QUESTIONS = {
    "fees": r"\b(fees?|cost|tuition)\b",
    "eligibility": r"\b(eligib\w*|criteria|qualification)\b",
    "duration": r"\b(duration|how long|how many years)\b",
}


def find_course_info(t: str, courses: list) -> Optional[dict]:
    """Search course list for a course match, returning the matching course object."""
    t_lower = t.lower()
    best_course, best_len = None, 0

    for course in courses:
        name = course.get("name", "")
        # Gather all possible identifiers/aliases for the course
        aliases = course.get("aliases", []) + [name, course.get("id", "")]
        for alias in aliases:
            if not alias:
                continue
            clean_alias = clean(alias)
            if len(clean_alias) < 3:     # skip very short words such as "it" or "me"
                continue
            # Whole-word match for keywords like 'bca', 'mca', 'bba', etc.
            if contains(t_lower, clean_alias):
                if len(clean_alias) > best_len:
                    best_course, best_len = course, len(clean_alias)

    return best_course


def course_info_reply(text: str, session_id: str, memory: dict) -> Optional[Dict]:
    t = clean(text)

    # 1. What is being asked? (fees / eligibility / duration)
    asked = next((q for q, pat in COURSE_QUESTIONS.items() if re.search(pat, t)), None)
    pending = memory.get("notes") if memory.get("notes") in COURSE_QUESTIONS else None
    asked = asked or pending

    # Not a fees / eligibility / duration question -> let the other handlers answer it
    if not asked:
        return None

    # 2. Which course? Look in the message first, then in the saved memory (Course: BCA)
    data = load_courses("course_info")
    matched_course = find_course_info(t, data)
    if not matched_course and memory.get("course"):
        matched_course = find_course_info(clean(memory.get("course")), data)

    # If we still don't have a course, ask the user to clarify the course
    if not matched_course:
        save_state(session_id, memory.get("course"), memory.get("semester"), memory.get("subject"), asked)
        return make_reply(
            f"Sure. Which course do you want the {asked} for?",
            "course_clarify",
            [c["name"] for c in data if isinstance(c, dict) and "name" in c],
            grounded=False,
        )

    c = matched_course
    course_name = c.get("name", "Course")
    save_state(session_id, course_name, memory.get("semester"), memory.get("subject"), None)
    
    line = {
        "fees": f"**Fee:** {c.get('fee', NOT_AVAILABLE)}",
        "eligibility": f"**Eligibility:** {c.get('eligibility', NOT_AVAILABLE)}",
        "duration": f"**Duration:** {c.get('duration', NOT_AVAILABLE)}",
    }.get(asked, f"**Fee:** {c.get('fee', NOT_AVAILABLE)}")

    extra = f"\nDuration: {c.get('duration')}" if asked == "fees" and c.get("duration") else ""
    note = (
        "*From the project's stored help-desk data. These figures are approximate. "
        "Please confirm with admissions: toll-free 1800-200-3575 or +91-95921-04444.*"
    )
    sources = [
        {"title": "CGC Admissions", "source_title": "Official", "url": "https://www.cgc.edu.in/admissions"},
        {"title": "CGC Contact Us", "source_title": "Official", "url": "https://www.cgc.edu.in/contact-us"},
    ]
    others = [w for w in COURSE_QUESTIONS if w != asked]
    return make_reply(
        f"### {course_name}: {asked}\n\n{line}{extra}\n\n{note}",
        f"course_{asked}",
        [f"{course_name} {w}" for w in others] + ["How to apply for admission?"],
        sources,
        verification="unconfirmed",
    )

# ------------------------------------------------------------------ 4. Main Entry Point
def handle_message(text: str, session_id: str, memory: dict) -> Optional[Dict]:
    """Return an answer dict, or None to fall back to broader chatbot handlers."""
    t = clean(text)

    # If the user asks a brand new general question, forget only the "waiting for an answer" flag.
    # The saved course / semester (Memory: BCA, Sem 6) are kept.
    if re.search(r"\b(department|college|library|ptu|syllabus|placement|contact|hostel)\b", t):
        save_state(session_id, memory.get("course"), memory.get("semester"), memory.get("subject"), None)
        memory = {**memory, "notes": None}

    from backend.official_answers import match_programs, answer_official, detect_intent
    progs = match_programs(text)
    intent = detect_intent(text)
    program_heard = bool(re.search(r"\b(?:tell me about|what (?:courses?|programs?|programmes?)|which (?:courses?|programs?|programmes?)|courses? are available|programmes? at cgc|about )\b", t))
    if progs and intent in {"programs", "about"} and program_heard:
        answer = answer_official(text, intent, memory, [])
        if answer:
            answer["intent"] = intent
            answer["actions"] = []
            return answer

    # 1. Scheme/batch lookups
    reply = schemes_reply(text)
    if reply:
        return reply

    # 2. Academic understanding
    reply = academic_reply(text, session_id, memory)
    if reply:
        return reply

    # 3. Course info (fees / eligibility / duration)
    reply = course_info_reply(text, session_id, memory) if not re.search(r"\bhostel\b", t) else None
    if reply:
        return reply

    if re.search(r"\b(fees?|scholarships?|fee structure)\b", t) and not re.search(r"\bhostel\b", t):
        return None

    # 4. Departmental & Topic sections (Library / PTU / CGC)
    # 4. Departmental & Topic sections (Library / PTU / CGC)
    for section, file_name in (("library", "library"), ("ptu", "ptu")):
        if re.search(AREA_WORDS[section], t):
            data = load(file_name)
            topic = pick_topic(t, data["topics"]) or (data["topics"][0] if section == "ptu" else None)
            if topic:
                save_state(session_id, memory.get("course"), memory.get("semester"), memory.get("subject"), None)
                return topic_reply(section, topic, data["title"])

    data = load("cgc_landran")
    
    # If the user is specifically asking about departments, colleges, or branches, prioritize that topic!
    if re.search(r"\b(department|colleges?|branches|schools?)\b", t):
        dept_topic = next((tp for tp in data.get("topics", []) if "department" in tp.get("id", "") or "college" in tp.get("id", "")), None)
        if dept_topic:
            save_state(session_id, memory.get("course"), memory.get("semester"), memory.get("subject"), None)
            return topic_reply("cgc", dept_topic, data["title"])

    topic = pick_topic(t, data["topics"])
    if topic:
        return topic_reply("cgc", topic, data["title"])

    return None