"""Facts taken from the official CGC Landran website (cgc.edu.in), read on 22 Oct 2026.
Nothing here is invented: if the site does not publish something (e.g. fee amounts), it is NOT listed.
Re-check these pages occasionally; the college can change them at any time."""

BASE = "https://www.cgc.edu.in/"
LINKS = {
    "home": BASE, "admissions": BASE + "admissions", "how_to_apply": BASE + "how-to-apply",
    "scholarship": BASE + "scholarship-2026", "financial_aid": BASE + "financial-aid",
    "contact": BASE + "contact-us", "placements": BASE + "placements", "placement_tracker": BASE + "placement-tracker",
    "library": BASE + "library", "overview": BASE + "overview", "approvals": BASE + "approvals-and-affiliations",
    "rankings": BASE + "awards-and-rankings", "exam_eval": BASE + "examination-evaluation",
    "tour": BASE + "virtual-tour", "rules": BASE + "college-rules-regulations", "find_program": BASE + "find-your-program",
    "pay_fee": "https://easypay.axisbank.co.in/easyPay/makePayment?mid=NTY3ODY%3D",
    "ptu": "https://ptu.ac.in/", "ptu_syllabus": "https://ptu.ac.in/syllabus",
    "lib_rules": BASE + "assets/documents/library/CGC%20LIBRARY%20RULES.pdf",
    "lib_digi": BASE + "assets/images/library/DIGI%20LIBRARY%20ANYTIME%20ANYWHERE.pdf",
    "lib_magazines": BASE + "assets/images/library/LIST%20OF%20MAGAZINES-CGC%202026.png",
    "lib_newspapers": BASE + "assets/images/library/LIST%20OF%20NEWSPAPERS-CGC%202026.png",
    "lib_journals": BASE + "assets/images/library/LIST%20OF%20PRINT%20JOURNALS-CGC%202026.png",
    # Central Library
    "library": "https://www.cgc.edu.in/library",
    "lib_digi": "https://www.cgc.edu.in/pdf/lib-digi.pdf",
    "lib_rules": "https://www.cgc.edu.in/pdf/lib-rules.pdf",
    "lib_journals": "https://www.cgc.edu.in/library/journals",
    "lib_magazines": "https://www.cgc.edu.in/library/magazines",
    "lib_newspapers": "https://www.cgc.edu.in/library/newspapers",
    
    # Department & Stream-Specific Portals
    "cec_library": "https://www.cgc.edu.in/cec-library",
    "coe_library": "https://www.cgc.edu.in/coe-library",
    "cbsa_library": "https://www.cbsa.edu.in/library",
    "cct_library": "https://www.cct.edu.in/library",
    "placement_library": "https://www.cgc.edu.in/placement-training-library",
}
CONTACT = {
    "address": "Chandigarh Group of Colleges, Sector 112, Landran, Mohali, Punjab 140307",
    "toll_free": "1800-200-3575",
    "admission": ["+91-95921-04444", "+91-95921-14444", "+91-95921-24444"],
    "whatsapp": "https://wa.me/919592214444",
}
GROUPS = {  # footer "Programs" pages
    "Engineering": "engineering", "Computer Applications": "computer-applications",
    "Business Management": "business-management", "Pharmacy": "pharmacy", "Biotechnology": "biotechnology",
    "Hotel Management": "hotel-management", "Commerce": "commerce", "Bachelor of Science": "bachelor-of-science",
}
# The programme list lives in data/cgc_programmes.json (edit that file, not this one).
# Layout of that file:  {"categories": [ {"category_name": "...", "courses": [ {"name", "cgc_url", "aliases", ...} ]} ]}
import json as _json, os as _os
_PROG_FILE = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "cgc_programmes.json")
PROGRAMS = []
for _cat in _json.load(open(_PROG_FILE, encoding="utf-8"))["categories"]:
    for _p in _cat.get("courses", _cat.get("programmes", [])):
        if not _p.get("cgc_url"):     # courses without a page link are only shown in the Courses tab
            continue
        PROGRAMS.append({
            "name": _p["name"],
            "url": _p["cgc_url"],
            "group": _cat.get("category_name", ""),
            "aliases": _p.get("aliases", []),   # words students may type, e.g. "btech cse"
        })
