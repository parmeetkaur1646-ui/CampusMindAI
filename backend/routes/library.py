from fastapi import APIRouter, Query
from typing import Optional
from backend.database import get_db_connection
from backend.official_data import LINKS

router = APIRouter(prefix="/api/library", tags=["Digital Library"])


@router.get("/resources")
def get_library_resources(
    category: Optional[str] = Query(None, description="Filter by category (e.g., e-books, e-journals, rules)"),
    department: Optional[str] = Query(None, description="Filter by department/stream (cec, coe, cbsa, cct, placement)")
):
    """Library resources and departmental platforms across CGC Landran."""
    resources = [
        {
            "id": "lib-digi", 
            "title": "Digi Library: anytime, anywhere", 
            "type": "E-resources guide (PDF)", 
            "category": "e-books",
            "department": "central",
            "description": "The library subscribes to e-books and e-journals. This is the official guide; login details are not published, so ask the library.",
            "access": "See the PDF", 
            "url": LINKS.get("lib_digi", "https://www.cgc.edu.in/assets/images/library/DIGI%20LIBRARY%20ANYTIME%20ANYWHERE.pdf")
        },
        {
            "id": "lib-journals", 
            "title": "Print journals subscribed, 2026", 
            "type": "Subscription list", 
            "category": "e-journals",
            "department": "central",
            "description": "Official list of print journals the library subscribes to this year.", 
            "access": "Central Library", 
            "url": LINKS.get("lib_journals", "https://www.cgc.edu.in/assets/images/library/LIST%20OF%20PRINT%20JOURNALS-CGC%202026.png")
        },
        {
            "id": "lib-magazines", 
            "title": "Magazines subscribed, 2026", 
            "type": "Subscription list", 
            "category": "e-journals",
            "department": "central",
            "description": "Official list of subscribed magazines.", 
            "access": "Central Library", 
            "url": LINKS.get("lib_magazines", "https://www.cgc.edu.in/assets/images/library/LIST%20OF%20MAGAZINES-CGC%202026.png")
        },
        {
            "id": "lib-newspapers", 
            "title": "Newspapers subscribed, 2026", 
            "type": "Subscription list", 
            "category": "e-journals",
            "department": "central",
            "description": "Official list of subscribed newspapers.", 
            "access": "Central Library", 
            "url": LINKS.get("lib_newspapers", "https://www.cgc.edu.in/assets/images/library/LIST%20OF%20NEWSPAPERS-CGC%202026.png")
        },
        {
            "id": "lib-rules", 
            "title": "Library Rules", 
            "type": "Official rules (PDF)", 
            "category": "rules",
            "department": "central",
            "description": "The library's published rules. Read this for membership, borrowing and conduct details.", 
            "access": "See the PDF", 
            "url": LINKS.get("lib_rules", "https://www.cgc.edu.in/assets/documents/library/CGC%20LIBRARY%20RULES.pdf")
        },
        {
            "id": "lib-main", 
            "title": "CGC Landran Central Library Platform", 
            "type": "Official page", 
            "category": "all",
            "department": "central",
            "description": "Fully automated with LIBSYS, CCTV-monitored, with over 1.25 lakh books on open shelves plus CDs, e-books, journals and e-journals.",
            "access": "Online", 
            "url": "https://www.cgc.edu.in/library"
        },
        {
            "id": "cec-lib",
            "title": "CEC Institute Library Collection",
            "type": "Department Portal",
            "category": "e-journals",
            "department": "cec",
            "description": "Central library facility catering to engineering students with vast technical book volumes, journals, and digital access.",
            "access": "Online",
            "url": "https://www.cecmohali.org/institute-library"
        },
        {
            "id": "cec-syllabus",
            "title": "Applied Sciences Scheme and Syllabus",
            "type": "Academic Portal",
            "category": "rules",
            "department": "cec",
            "description": "Course schemes, syllabi, and academic documentation for Applied Sciences and first-year engineering.",
            "access": "Online",
            "url": "https://www.cecmohali.org/applied-sciences-scheme-and-syllabus"
        },
        {
            "id": "coe-lib",
            "title": "COE Library Desk",
            "type": "Research Portal",
            "category": "e-journals",
            "department": "coe",
            "description": "Dedicated resource center providing academic textbooks, reference materials, and digital repositories for engineering programs.",
            "access": "Online",
            "url": "https://www.cgccoe.org/library"
        },
        {
            "id": "cbsa-lib",
            "title": "CBSA E-Libraries & Journals",
            "type": "Department Portal",
            "category": "e-journals",
            "department": "cbsa",
            "description": "Access portal for management and commerce e-journals, business databases, case studies, and digital periodicals.",
            "access": "Online",
            "url": "https://cbsmohali.org/e-libraries-journals"
        },
        {
            "id": "cct-lib",
            "title": "CCT Library Directory",
            "type": "Department Portal",
            "category": "e-journals",
            "department": "cct",
            "description": "Equipped with specialized technical volumes, project reports, and computing resources for technology courses.",
            "access": "Online",
            "url": "https://www.cctmohali.org/library"
        },
        {
            "id": "ccp-lib",
            "title": "CCP Library & Resources",
            "type": "Department Portal",
            "category": "e-journals",
            "department": "ccp",
            "description": "Specialized pharmaceutical and medical research library containing pharmacology textbooks, research papers, and digital subscriptions.",
            "access": "Online",
            "url": "https://www.ccpmohali.org/"
        },
        {
            "id": "cchmct-lib",
            "title": "CCHMCT Library & Resource Centre",
            "type": "Department Portal",
            "category": "e-journals",
            "department": "cchmct",
            "description": "Collection covering culinary arts, hospitality management, tourism, food production, and recipe archives.",
            "access": "Online",
            "url": "https://www.cchmct.org/"
        },
        {
            "id": "placement-lib",
            "title": "CGC 360° Training & Placement Program",
            "type": "Skill Platform",
            "category": "training",
            "department": "placement",
            "description": "Comprehensive online course library for placements, including LinkedIn Learning & AMCAT preparation modules.",
            "access": "Online",
            "url": LINKS.get("placement_library", "https://www.cgc.edu.in/")
        },
    ]

    if category and category != "all":
        resources = [r for r in resources if r["category"] in (category, "all")]

    if department:
        resources = [r for r in resources if r["department"] == department.lower() or r["department"] == "central"]

    return {
        "institution": "CGC Landran Digital Libraries",
        "official_url": "https://www.cgc.edu.in/library",
        "timings": "Monday to Saturday, 8:30 AM to 8:00 PM (Reading hall up to 10:00 PM during exams). See the Library Rules PDF or ask the library.",
        "filtered_by": {"category": category, "department": department},
        "resources": resources,
    }


@router.get("/rules")
def get_library_rules():
    return {
        "rules": [
            "From the official CGC Library Rules PDF:",
            "Card: Every student needs a stamp-size photograph for the identity-cum-library card. It is non-transferable and must be carried in the library.",
            "Borrowing: Graduate and postgraduate students can issue 3 books for 21 days. A fine is charged for late return.",
            "Reference books and magazines can only be read inside the library.",
            "Belongings: Bags and personal items must be left at the property counter.",
            "Conduct: No eating, sleeping, or smoking. Keep silence and switch off mobile phones."
        ],
        "official_link": "https://www.cgc.edu.in/assets/documents/library/CGC%20LIBRARY%20RULES.pdf",
    }