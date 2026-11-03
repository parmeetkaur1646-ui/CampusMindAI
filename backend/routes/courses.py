"""Course Explorer data. Everything comes from data/*.json.

To change the Courses page, edit data/cgc_programmes.json (one block per course, grouped in categories).
Optional: data/ptu_syllabus_index.json can hold a "batches" text for a course (shown on the Courses page).
"""
from typing import Optional
from fastapi import APIRouter, Query
from backend.chat_engine import load, load_courses

router = APIRouter(prefix="/api/courses", tags=["Course Explorer"])
NOT_YET = "Information not available yet"


def build_departments():
    # PTU syllabus batches (optional): look up by course name
    ptu_batches = {c.get("name"): c.get("batches") for c in load_courses("ptu_syllabus_index")}

    departments = []
    categories = load("cgc_programmes").get("categories", [])

    for number, category in enumerate(categories, start=1):
        programs = []
        for course in category.get("courses", category.get("programmes", [])):
            programs.append({
                "name": course.get("name", NOT_YET),
                "level": course.get("level") or NOT_YET,
                "duration": course.get("duration") or NOT_YET,
                "eligibility": course.get("eligibility") or NOT_YET,
                "fee": course.get("fee") or NOT_YET,
                # True when the details come from our own data file (so the page shows "please confirm officially")
                "approximate": bool(course.get("fee") or course.get("eligibility") or course.get("duration")),
                "features": course.get("note", ""),
                "cgc_url": course.get("cgc_url"),
                "ptu_batches": ptu_batches.get(course.get("name")),
                "aliases": course.get("aliases", []),
            })

        department_name = category.get("category_name") or category.get("name") or f"Department {number}"
        departments.append({
            "department_code": department_name.replace(" ", "").upper()[:4],
            "department": department_name,
            "category_url": category.get("category_url", ""),
            "description": category.get("description", ""),
            "programs": programs,
        })

    return departments


@router.get("")
def get_courses(department: Optional[str] = Query(None)):
    departments = build_departments()
    if department:
        departments = [
            d for d in departments
            if department.lower() in (d["department_code"].lower(), d["department"].lower())
        ]
    return {"count": len(departments), "departments": departments}


@router.get("/search")
def search_courses(q: Optional[str] = Query(None, description="Search term for courses or aliases")):
    departments = build_departments()
    if not q:
        return {"query": q, "results": []}

    query = q.lower().strip()
    matched_programs = []
    for dept in departments:
        for prog in dept["programs"]:
            if query in prog["name"].lower() or any(query in alias.lower() for alias in prog.get("aliases", [])):
                matched_programs.append({**prog, "department": dept["department"]})
    return {"query": q, "count": len(matched_programs), "results": matched_programs}
