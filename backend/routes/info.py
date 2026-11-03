"""Serves the editable JSON data files to the website (Academic, Library, PTU, CGC Landran sections)."""
from fastapi import APIRouter, HTTPException
from backend.chat_engine import load

router = APIRouter(prefix="/api", tags=["Sections"])


@router.get("/academic/tree")
def academic_tree():
    """All courses > semesters > subjects > syllabus/notes/important questions/quiz."""
    return load("academic")


@router.get("/info/{section}")
def section_info(section: str):
    """section is one of: library, ptu, cgc"""
    names = {"library": "library", "ptu": "ptu", "cgc": "cgc_landran"}
    if section not in names:
        raise HTTPException(status_code=404, detail="Unknown section")
    return load(names[section])
