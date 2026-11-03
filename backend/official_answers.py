"""Deterministic, source-based answers. Each question type has its own answer, and anything the
official sites do not publish is said plainly instead of being guessed."""
import re
from typing import Dict, List, Optional

from backend.official_data import CONTACT, GROUPS, LINKS, PROGRAMS, BASE

_EXHAUSTIVE_PROGRAM_CATALOG = [
    {
        "category_name": "1. Engineering & Technology (B.Tech & M.Tech)",
        "category_url": "https://www.cgc.edu.in/engineering",
        "description": "B.Tech (4 Years), B.Tech Lateral Entry (LEET - 3 Years), and M.Tech (2 Years)[cite: 1].",
        "courses": [
            {"name": "Computer Science & Engineering (CSE)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-cse"},
            {"name": "Information Technology (IT)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-it"},
            {"name": "Artificial Intelligence & Machine Learning (AI & ML)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-in-artificial-intelligence-and-machine-learning"},
            {"name": "Artificial Intelligence & Data Science (AI & DS)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-in-artificial-intelligence-and-data-science"},
            {"name": "CSE (Cyber Security)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-cse-cyber-security"},
            {"name": "CSE (Data Science)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-cse-data-science"},
            {"name": "CSE (IoT & Cyber Security including Blockchain)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-cse-iot-cyber-security-including-blockchain"},
            {"name": "Electronics & Computer Engineering", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-electronics-and-computer-engineering"},
            {"name": "Robotics & Artificial Intelligence", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-robotics-and-ai"},
            {"name": "Electronics & Communication Engineering (ECE)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-electronics-and-communication-engineering"},
            {"name": "Mechanical Engineering (ME)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-tech-me"},
            {"name": "B.Tech Lateral Entry (LEET)", "level": "Lateral Entry", "duration": "3 Years", "url": "https://www.cgc.edu.in/b-tech-leet"},
            {"name": "M.Tech (CSE, IT, ECE, Mechanical)", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/m-tech-cse"}
        ]
    },
    {
        "category_name": "2. Computer Applications & Multimedia",
        "category_url": "https://www.cgc.edu.in/computer-applications",
        "description": "Undergraduate and postgraduate computing and multimedia programs[cite: 1].",
        "courses": [
            {"name": "Bachelor of Computer Applications (BCA)", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bca"},
            {"name": "BCA LEET", "level": "Lateral Entry", "duration": "2 Years", "url": "https://www.cgc.edu.in/bca"},
            {"name": "B.Sc. (Multimedia)", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bsc-multimedia"},
            {"name": "B.Sc. (Graphic & Web Designing)", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bsc-graphic-web-designing"},
            {"name": "Master of Computer Applications (MCA)", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/mca"}
        ]
    },
    {
        "category_name": "3. Business Management & Commerce",
        "category_url": "https://www.cgc.edu.in/business-management",
        "description": "Undergraduate and postgraduate business management and commerce programs[cite: 1].",
        "courses": [
            {"name": "Bachelor of Business Administration (BBA)", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bba"},
            {"name": "Bachelor of Commerce - Hons (B.Com Hons)", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bachelor-of-commerce"},
            {"name": "Master of Business Administration (MBA)", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/mba"},
            {"name": "MBA in Digital Marketing", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/mba-digital-marketing"},
            {"name": "Master of Commerce (M.Com)", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/business-management"}
        ]
    },
    {
        "category_name": "4. Pharmacy & Paramedical Sciences",
        "category_url": "https://www.cgc.edu.in/pharmacy",
        "description": "Undergraduate, doctoral, postgraduate, and diploma pharmacy programs[cite: 1].",
        "courses": [
            {"name": "Bachelor of Pharmacy (B.Pharm)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/b-pharmacy"},
            {"name": "B.Pharm LEET", "level": "Lateral Entry", "duration": "3 Years", "url": "https://www.cgc.edu.in/b-pharmacy-leet"},
            {"name": "Doctor of Pharmacy (Pharm.D)", "level": "Doctoral", "duration": "6 Years", "url": "https://www.cgc.edu.in/pharm-d-doctor-of-pharmacy"},
            {"name": "Master of Pharmacy (M.Pharm)", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/m-pharmacy"},
            {"name": "Diploma in Pharmacy (D.Pharm)", "level": "Diploma", "duration": "2 Years", "url": "https://www.cgc.edu.in/pharmacy"}
        ]
    },
    {
        "category_name": "5. Biotechnology & Basic Sciences",
        "category_url": "https://www.cgc.edu.in/biotechnology",
        "description": "Undergraduate and postgraduate biotechnology and basic sciences programs[cite: 1].",
        "courses": [
            {"name": "B.Sc. Biotechnology", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bsc-biotechnology"},
            {"name": "B.Sc. Artificial Intelligence & Machine Learning", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/bsc-artificial-intelligence-machine-learning"},
            {"name": "B.Sc. Cyber Security", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/biotechnology"},
            {"name": "B.Sc. (Hons) Microbiology", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/biotechnology"},
            {"name": "M.Sc. Biotechnology", "level": "Postgraduate", "duration": "2 Years", "url": "https://www.cgc.edu.in/msc-biotechnology"}
        ]
    },
    {
        "category_name": "6. Hospitality, Hotel Management & Tourism",
        "category_url": "https://www.cgc.edu.in/hotel-management",
        "description": "Undergraduate, nutrition, and diploma hospitality programs.",
        "courses": [
            {"name": "Bachelor of Hotel Management and Catering Technology (BHMCT)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/bsc-hmct"},
            {"name": "Bachelor of Tourism and Travel Management (BTTM)", "level": "Undergraduate", "duration": "4 Years", "url": "https://www.cgc.edu.in/bttm-bachelor-of-tourism-and-travel-management"},
            {"name": "B.Sc. Hospitality & Hotel Administration (HHA)", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/hotel-management"},
            {"name": "B.Sc. (Honors) Nutrition & Dietetics", "level": "Undergraduate", "duration": "3 Years", "url": "https://www.cgc.edu.in/b-sc-nutrition-and-dietetics"},
            {"name": "Diploma in Food Production", "level": "Diploma", "duration": "1-2 Years", "url": "https://www.cgc.edu.in/hotel-management"},
            {"name": "Diploma in Bakery & Confectionery", "level": "Diploma", "duration": "1-2 Years", "url": "https://www.cgc.edu.in/hotel-management"}
        ]
    }
]

# --- Structured CGC Catalog Data for Course-Wise Fees ---
_COURSE_FEES_CATALOG = {
    "Engineering — B.Tech / M.Tech": [
        {"name": "Computer Science Engineering (CSE)", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-cse"},
        {"name": "Information Technology (IT)", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-it"},
        {"name": "Artificial Intelligence and Machine Learning (AI & ML)", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-in-artificial-intelligence-and-machine-learning"},
        {"name": "Artificial Intelligence and Data Science (AI & DS)", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-in-artificial-intelligence-and-data-science"},
        {"name": "Electronics and Communication Engineering (ECE)", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-electronics-and-communication-engineering"},
        {"name": "Mechanical Engineering", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-me"},
        {"name": "CSE — Data Science", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-cse-data-science"},
        {"name": "CSE — Cyber Security", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-cse-cyber-security"},
        {"name": "CSE — IoT and Cyber Security, including Blockchain", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-cse-iot-cyber-security-including-blockchain"},
        {"name": "Robotics and Artificial Intelligence", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-robotics-and-ai"},
        {"name": "Electronic and Computer Engineering", "duration": "4 Years", "fee": "Approx Rs 5.04 to 6.72 Lakh total", "url": "https://www.cgc.edu.in/b-tech-electronics-and-computer-engineering"},
        {"name": "M.Tech in CSE, IT, ECE and Mechanical Engineering", "duration": "2 Years", "fee": "Approx Rs 1.5 to 2.5 Lakh total", "url": "https://www.cgc.edu.in/m-tech-cse"},
        {"name": "B.Tech lateral-entry (LEET) options", "duration": "3 Years", "fee": "Approx Rs 3.8 to 5.0 Lakh total", "url": "https://www.cgc.edu.in/b-tech-leet"}
    ],
    "Computer Applications": [
        {"name": "BCA — Bachelor of Computer Applications", "duration": "3 Years", "fee": "Approx Rs 3.06 Lakh total", "url": "https://www.cgc.edu.in/bca"},
        {"name": "BCA LEET", "duration": "2 Years", "fee": "Approx Rs 2.0 to 2.5 Lakh total", "url": "https://www.cgc.edu.in/bca"},
        {"name": "MCA — Master of Computer Applications", "duration": "2 Years", "fee": "Approx Rs 2.5 to 3.2 Lakh total", "url": "https://www.cgc.edu.in/mca"}
    ],
    "Business and Commerce": [
        {"name": "BBA", "duration": "3 Years", "fee": "Approx Rs 3.06 Lakh total", "url": "https://www.cgc.edu.in/bba"},
        {"name": "MBA", "duration": "2 Years", "fee": "Approx Rs 3.36 Lakh total", "url": "https://www.cgc.edu.in/mba"},
        {"name": "MBA in Digital Marketing", "duration": "2 Years", "fee": "Approx Rs 3.36 Lakh total", "url": "https://www.cgc.edu.in/mba-digital-marketing"},
        {"name": "B.Com. (Hons.)", "duration": "3 Years", "fee": "Approx Rs 3.06 Lakh total", "url": "https://www.cgc.edu.in/bachelor-of-commerce"}
    ],
    "Pharmacy": [
        {"name": "B.Pharm", "duration": "4 Years", "fee": "Approx Rs 4.5 to 5.2 Lakh total", "url": "https://www.cgc.edu.in/b-pharmacy"},
        {"name": "B.Pharm LEET", "duration": "3 Years", "fee": "Approx Rs 3.5 to 4.0 Lakh total", "url": "https://www.cgc.edu.in/b-pharmacy-leet"},
        {"name": "Pharm.D", "duration": "6 Years", "fee": "Approx Rs 9.0 to 11.0 Lakh total", "url": "https://www.cgc.edu.in/pharm-d-doctor-of-pharmacy"},
        {"name": "Pharm.D (Post Baccalaureate)", "duration": "3 Years", "fee": "Approx Rs 4.5 to 5.5 Lakh total", "url": "https://www.cgc.edu.in/pharm-d-post-buccalureate"},
        {"name": "M.Pharm in Pharmaceutics", "duration": "2 Years", "fee": "Approx Rs 2.5 to 3.0 Lakh total", "url": "https://www.cgc.edu.in/m-pharmacy"},
        {"name": "M.Pharm in Pharmacology", "duration": "2 Years", "fee": "Approx Rs 2.5 to 3.0 Lakh total", "url": "https://www.cgc.edu.in/mpharma-pharmacology"},
        {"name": "M.Pharm in Pharmacy Practice", "duration": "2 Years", "fee": "Approx Rs 2.5 to 3.0 Lakh total", "url": "https://www.cgc.edu.in/m-pharm-in-pharmacy-practice"},
        {"name": "M.Pharm in Regulatory Affairs", "duration": "2 Years", "fee": "Approx Rs 2.5 to 3.0 Lakh total", "url": "https://www.cgc.edu.in/m-pharm-pharmaceutical-regulatory-affairs"}
    ],
    "Science and Biotechnology": [
        {"name": "B.Sc. Biotechnology", "duration": "3 Years", "fee": "Approx Rs 3.06 Lakh total", "url": "https://www.cgc.edu.in/bsc-biotechnology"},
        {"name": "M.Sc. Biotechnology", "duration": "2 Years", "fee": "Approx Rs 1.3 to 1.84 Lakh total", "url": "https://www.cgc.edu.in/msc-biotechnology"},
        {"name": "B.Sc. Artificial Intelligence and Machine Learning", "duration": "3 Years", "fee": "Approx Rs 2.8 to 3.1 Lakh total", "url": "https://www.cgc.edu.in/bsc-artificial-intelligence-machine-learning"},
        {"name": "B.Sc. Multimedia", "duration": "3 Years", "fee": "Approx Rs 2.58 Lakh total", "url": "https://www.cgc.edu.in/bsc-multimedia"},
        {"name": "B.Sc. Graphics and Web Designing", "duration": "3 Years", "fee": "Approx Rs 2.58 Lakh total", "url": "https://www.cgc.edu.in/bsc-graphic-web-designing"},
        {"name": "B.Sc. (Hons.) Nutrition and Dietetics", "duration": "3 Years", "fee": "Approx Rs 3.01 Lakh total", "url": "https://www.cgc.edu.in/b-sc-nutrition-and-dietetics"}
    ],
    "Hotel Management and Tourism": [
        {"name": "BHMCT — Hotel Management and Catering Technology", "duration": "4 Years", "fee": "Approx Rs 3.5 to 4.2 Lakh total", "url": "https://www.cgc.edu.in/bsc-hmct"},
        {"name": "BTTM — Bachelor of Tourism and Travel Management", "duration": "4 Years", "fee": "Approx Rs 3.0 Lakh total", "url": "https://www.cgc.edu.in/bttm-bachelor-of-tourism-and-travel-management"},
        {"name": "BMS — Airlines, Tourism and Hospitality", "duration": "3 Years", "fee": "Approx Rs 3.0 Lakh total", "url": "https://www.cgc.edu.in/bachelor-of-management-studies-airlines-tourism-hospitality"},
        {"name": "B.Voc. Hospitality and Catering Management", "duration": "3 Years", "fee": "Approx Rs 2.5 Lakh total", "url": "https://www.cgc.edu.in/bachelor-of-vocation-hospitality-and-catering-management"}
    ]
}

# --- Structured CGC Catalog Data for Course-Wise Placements ---
_COURSE_PLACEMENTS_CATALOG = {
    "Engineering — B.Tech / M.Tech": [
        {"name": "Computer Science Engineering (CSE) / IT / AI & ML / AI & DS", "highest_package": "₹1.14 Cr PA (IT/AI & ML: ₹44.15 LPA)", "recruiters": "Amazon, Google, Microsoft, Dell, IBM", "url": "https://www.cgc.edu.in/b-tech-cse"},
        {"name": "Electronics and Communication Engineering (ECE)", "highest_package": "₹41.00 LPA", "recruiters": "Wipro, Accenture, Capgemini, Tech Mahindra", "url": "https://www.cgc.edu.in/b-tech-electronics-and-communication-engineering"},
        {"name": "Mechanical Engineering", "duration": "4 Years", "highest_package": "₹12.00 LPA", "recruiters": "L&T, Tata Motors, Mahindra", "url": "https://www.cgc.edu.in/b-tech-me"},
        {"name": "M.Tech (CSE, IT, ECE, Mechanical)", "highest_package": "₹33.50 LPA (ECE & Mech: ₹33.50 LPA | CSE & IT: ₹20.00 LPA)", "recruiters": "Core Tech & Research Firms", "url": "https://www.cgc.edu.in/m-tech-cse"}
    ],
    "Computer Applications": [
        {"name": "BCA / MCA (Computer Applications)", "highest_package": "₹36.50 LPA", "recruiters": "Cognizant, Infosys, Tech Mahindra, Wipro", "url": "https://www.cgc.edu.in/bca"}
    ],
    "Business and Commerce": [
        {"name": "MBA (General & Digital Marketing)", "highest_package": "₹20.00 – ₹22.00 LPA", "recruiters": "Deloitte, KPMG, HDFC Bank, ICICI Bank", "url": "https://www.cgc.edu.in/mba"},
        {"name": "BBA & B.Com. (Hons.)", "highest_package": "BBA: ₹13.93 LPA | B.Com: ₹17.03 LPA", "recruiters": "Ernst & Young (EY), Genpact, Deloitte", "url": "https://www.cgc.edu.in/bba"}
    ],
    "Pharmacy": [
        {"name": "B.Pharm / M.Pharm / Pharm.D.", "highest_package": "B.Pharm: ₹18.00 LPA | M.Pharm: ₹14.00 LPA", "recruiters": "Cipla, Sun Pharma, Dr. Reddy's Laboratories", "url": "https://www.cgc.edu.in/b-pharmacy"}
    ],
    "Science and Biotechnology": [
        {"name": "B.Sc. / M.Sc. Biotechnology & Specialized Science", "highest_package": "₹18.00 LPA", "recruiters": "Panacea Biotec, Biocon, Lal PathLabs", "url": "https://www.cgc.edu.in/bsc-biotechnology"}
    ],
    "Hotel Management and Tourism": [
        {"name": "BHMCT / BTTM / BMS / B.Voc. Hospitality", "highest_package": "BHMCT: ₹7.50 LPA | BTTM: ₹5.00 LPA", "recruiters": "The Taj Group, Marriott, Hyatt, ITC Hotels", "url": "https://www.cgc.edu.in/bsc-hmct"}
    ]
}

# --- Structured CGC Catalog Data for Library Details & Resources ---
_LIBRARY_CATALOG = {
    "sections": [
        {"name": "Central Library Network", "volumes": "1.25 Lakh+ books on open shelves", "software": "LIBSYS automated cataloging, CCTV security monitoring", "url": "https://www.cgc.edu.in/library"},
        {"name": "CEC Institute Library", "volumes": "Engineering & Technology collections", "url": "https://www.cecmohali.org/institute-library"},
        {"name": "COE Library", "volumes": "College of Engineering resources", "url": "https://www.cgccoe.org/library"},
        {"name": "CCT Library", "volumes": "9,495+ volumes and 1,217+ titles", "url": "https://www.cctmohali.org/library"},
        {"name": "CCP Library", "volumes": "Pharmacy & Clinical Research library", "url": "https://www.ccpmohali.org/"},
        {"name": "CCHMCT Library", "volumes": "Hotel Management & Catering collection", "url": "https://www.cchmct.org/"}
    ],
    "rules": {
        "timings": "Monday to Saturday, 8:30 AM to 8:00 PM (Reading hall open up to 10:00 PM during mid-semester and end-semester examinations).",
        "borrowing": "Graduate and postgraduate students can issue 3 books for 21 days. Reference books and magazines are for use inside the library only.",
        "membership_card": "Identity-cum-library card requires a stamp-size photograph, is non-transferable, and must be carried at all times.",
        "fines_and_lost": "Late return incurs a fine. Lost books must be reported immediately, to be replaced or paid for within a week of the due date.",
        "conduct": "Bags and personal items must be deposited at the property counter. Complete silence, no eating, sleeping, or smoking; mobile phones must be switched off."
    },
    "digital_resources": [
        {"name": "EBSCOhost & E-Books", "details": "2.49 Lakh+ e-books & comprehensive multi-disciplinary databases", "url": "https://www.cgc.edu.in/assets/images/library/DIGI%20LIBRARY%20ANYTIME%20ANYWHERE.pdf"},
        {"name": "National Digital Library of India (NDLI)", "details": "Institutional Club member providing access to 45+ million digital learning resources", "url": "https://www.cgc.edu.in/assets/images/library/DIGI%20LIBRARY%20ANYTIME%20ANYWHERE.pdf"},
        {"name": "DELNET (Developing Library Network)", "details": "Inter-Library Loan (ILL) and document delivery services across partner libraries", "url": "https://www.cgc.edu.in/assets/images/library/DIGI%20LIBRARY%20ANYTIME%20ANYWHERE.pdf"},
        {"name": "Subscribed Print Journals, Magazines & Newspapers (2026)", "details": "Active subscriptions including technical journals, business magazines, and leading dailies", "url": "https://www.cgc.edu.in/library"}
    ]
}

_ALIASES = [
    (r"\bpharm\.?\s?d\b", "pharmd"), (r"\bb\.?\s?pharm\w*\b", "bpharm"), (r"\bm\.?\s?pharm\w*\b", "mpharm"),
    (r"\bb\.?\s?tech\b", "btech"), (r"\bm\.?\s?tech\b", "mtech"), (r"\bb\.?\s?sc\b", "bsc"), (r"\bm\.?\s?sc\b", "msc"),
    (r"\bb\.?\s?com\b", "bcom"), (r"\bb\.?\s?voc\b", "bvoc"),
    (r"\bbachelor of computer applications?\b", "bca"), (r"\bmaster of computer applications?\b", "mca"),
    (r"\bbachelor of business administration\b", "bba"), (r"\bmaster of business administration\b", "mba"),
    (r"\bcomputer science( and| &)?( engineering)?\b", "cse"), (r"\binformation technology\b", "infotech"),
    (r"\bmachine learning\b", "ml"), (r"\bartificial intelligence\b", "ai"), (r"\bdata science\b", "ds"),
    (r"\belectronics (and|&) communication( engineering)?\b", "ece"), (r"\bmechanical( engineering)?\b", "mech"),
    (r"\bcyber ?security\b", "cyber"), (r"\binternet of things\b", "iot"), (r"\bbiotechnology\b", "biotech"),
    (r"\blateral entry\b", "leet"),
]
_DEGREE = {"btech", "mtech", "bpharm", "mpharm", "pharmd", "bsc", "msc", "bca", "mca", "bba", "mba", "bcom", "bvoc"}
_BRANCH = {"cse", "ece", "mech", "infotech", "robotic"}


def _stem(w):
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def tokens(text: str) -> List[str]:
    t = text.lower()
    t = re.sub(r"\bc\+\+\b", "cpp", t)
    for pat, rep in _ALIASES:
        t = re.sub(pat, rep, t)
    t = re.sub(r"\b(btech|mtech) it\b", r"\1 infotech", t)
    toks = [_stem(w) for w in re.findall(r"[a-z0-9]+", t)]
    if not (_DEGREE & set(toks)) and _BRANCH & set(toks):
        toks.append("btech")
    return toks


# A question mentions a "family" of programmes when it contains one of these words (e.g. "btech")
_FAMILY = ("btech", "mtech", "bpharm", "mpharm", "pharmd", "bsc", "msc")
# word typed by the student -> text that must be inside the category name in data/cgc_programmes.json
_GROUP_WORD = {"engineering": "engineering", "pharmacy": "pharmacy", "hotel": "hotel",
               "management": "business", "biotech": "biotechnology", "commerce": "commerce"}

# Words that appear in normal sentences ("tell me about..."), so they can never identify a programme alone
_TOO_COMMON = {"it", "me"}

# Every programme in data/cgc_programmes.json lists "aliases" (words students may type).
# Turn each alias into a set of words that must ALL be present in the question.
for _p in PROGRAMS:
    _sets = [frozenset(tokens(alias)) for alias in _p.get("aliases", [])]
    _p["musts"] = [words for words in _sets if words and not (words & _TOO_COMMON)]


def _alias_score(program: Dict, toks: set) -> int:
    """How many words of the longest matching alias are in the question (0 = no match)."""
    return max((len(words) for words in program["musts"] if words <= toks), default=0)


def match_programs(text: str) -> List[Dict]:
    toks = set(tokens(text))
    scored = [(p, _alias_score(p, toks)) for p in PROGRAMS]
    exact = [(p, score) for p, score in scored if score]
    if exact:
        best = max(score for _, score in exact)
        return [p for p, score in exact if score == best]
    out = []
    for tok in _FAMILY:
        if tok in toks:
            out += [p for p in PROGRAMS if any(tok in words for words in p["musts"]) and p not in out]
    for tok, part in _GROUP_WORD.items():
        if tok in toks:
            out += [p for p in PROGRAMS if part in p["group"].lower() and p not in out]
    if {"computer", "application"} <= toks:
        out += [p for p in PROGRAMS if "computer applications" in p["group"].lower() and p not in out]
    return out


# ---------- intent ----------
_RULES = [
    ("greeting", r"^\s*(hi|hello|hey|namaste|good (morning|afternoon|evening))\b[\s!.?]*$"),
    ("fees", r"\bfees?\b|\btuition\b|\bcost\b|\bcharges\b|\bfee structure\b"),
    ("scholarship", r"\bscholarships?\b|\bfinancial aid\b|\bconcession\b"),
    ("library", r"\blibrar|\bbooks?\b|\be-?books?\b|\bjournals?\b|\bmagazines?\b|\bnewspapers?\b|\bdigi\b"),
    ("syllabus", r"\bsyllabus\b|\bcurriculum\b|\bscheme\b|\bsubjects?\b|\bsemester\b|\bsem\b|\bpaper code\b"),
    ("admissions", r"\badmissions?\b|\beligib|\bhow to apply\b|\bapply\b|\bregistration\b|\bleet\b|\blateral\b|\bcounsel"),
    ("placements", r"\bplacements?\b|\bpackages?\b|\brecruit|\bcompan(y|ies)\b|\bsalary\b|\bjobs?\b|\bhighest\b"),
    ("contact", r"\bcontact\b|\bphone\b|\bhelpline\b|\bnumber\b|\bcall\b|\bemail\b|\baddress\b|\blocation\b|\bwhere is\b|\bwhatsapp\b|\breach\b"),
    ("exam", r"\bexams?\b|\bexamination\b|\bresults?\b|\bdate ?sheet\b|\badmit card\b|\bre-?appear\b|\bcgpa\b|\battendance\b|\bmarks\b"),
    ("campus", r"\bhostel\b|\btransport\b|\bbus\b|\bmess\b|\bcanteen\b|\bcampus\b|\binfrastructure\b|\bfacilit"),
    ("about", r"\babout\b|\boverview\b|\baffiliat|\baccredit|\bnaac\b|\bnba\b|\branking|\bestablished\b|\bapproved\b"),
    ("programs", r"\bcourses?\b|\bprograms?\b|\bprogrammes?\b|\bdepartments?\b|\bbranches\b|\bdegrees?\b|\boffered\b|\bstreams?\b|\bcolleges?\b"),
    ("study", r"\bnotes?\b|\bquiz\b|\brevision\b|\bstudy\b|\bpractice\b|\bexplain\b|\bwhat is\b|\bhow does\b|\bdifference between\b"),
]


def detect_intent(query: str) -> Optional[str]:
    q = query.lower()
    for name, pat in _RULES:
        if re.search(pat, q):
            if name == "about" and match_programs(query):
                continue
            return name
    return "programs" if match_programs(query) else None


# ---------- answer building ----------
def _src(*keys):
    titles = {"admissions": "CGC Admissions", "how_to_apply": "How to Apply", "scholarship": "Scholarship Details",
              "financial_aid": "Financial Aid", "contact": "CGC Contact Us", "placements": "CGC Placements",
              "placement_tracker": "Placement Tracker", "library": "CGC Library", "overview": "About CGC (Overview)",
              "approvals": "Approval & Affiliation", "rankings": "Awards & Rankings", "exam_eval": "Examination Evaluation",
              "tour": "CGC 360° Campus Tour", "pay_fee": "Pay Fee Online (official)", "ptu": "IKGPTU (PTU) website",
              "ptu_syllabus": "PTU Syllabus Portal", "home": "CGC Landran website", "rules": "College Rules & Regulations",
              "lib_rules": "Library Rules (PDF)", "lib_digi": "Digi Library (PDF)", "lib_magazines": "Magazines subscribed 2026",
              "lib_newspapers": "Newspapers subscribed 2026", "lib_journals": "Print journals subscribed 2026",
              "find_program": "Find your Program"}
    return [{"title": titles[k], "source_title": "Official", "url": LINKS[k]} for k in keys]


def _prog_src(progs):
    return [{"title": p["name"] + " (official page)", "source_title": "CGC Landran", "url": p["url"]} for p in progs[:4]]


def _bullets(progs):
    return "\n".join(f"- [{p['name']}]({p['url']})" for p in progs)


def _helpline():
    return (f"- Toll-free: **{CONTACT['toll_free']}**\n- Admission help: " + " / ".join(CONTACT["admission"]) +
            f"\n- [WhatsApp]({CONTACT['whatsapp']})")


def _out(answer, sources, follow, grounded=True):
    gap = re.search(r"could not find|couldn't find|won't guess|not available yet|can't show|can't read", answer, re.I)
    return {"answer": answer, "sources": sources, "follow_up_suggestions": follow, "grounded": grounded,
            "verification": "verified" if (grounded and not gap) else "none"}


_SEM = re.compile(r"\b(?:sem(?:ester)?)\s*([1-9])\b|\b([1-9])(?:st|nd|rd|th)?\s*sem(?:ester)?\b", re.I)


def answer_official(query: str, intent: str, ctx: Dict, kb_docs: Optional[List[Dict]] = None) -> Optional[Dict]:
    progs = match_programs(query)
    ctx_progs = match_programs(ctx.get("course") or "") if intent == "syllabus" else []
    q = query.lower()

    if intent == "greeting":
        return _out("Hello! I'm **CampusMind AI**, the official intelligent digital campus assistant for Chandigarh Group of Colleges (CGC), Landran, affiliated with I.K. Gujral Punjab Technical University (IKGPTU). Ask me about fees, admissions, programmes, syllabus sources, the library, placements or contacts, and I'll answer from the official CGC and PTU websites.", [],
                    ["BBA fees", "How to apply for admission?", "Library rules", "BCA syllabus semester 5"], False)

    if intent == "fees":
        matched_courses = []
        for cat_name, courses in _COURSE_FEES_CATALOG.items():
            for c in courses:
                c_name_lower = c["name"].lower()
                if any(alias in q for alias in [c_name_lower, cat_name.lower()]) or any(word in q for word in tokens(c["name"])):
                    matched_courses.append((cat_name, c))

        if matched_courses and any(k in q for k in ["btech", "bca", "mca", "bba", "mba", "bpharm", "pharmd", "bsc", "msc", "bcom", "bhmct", "bttm", "bms", "bvoc", "engineering", "pharmacy", "computer", "business", "science", "hotel"]):
            text = "### Course-Wise Fee Structure at CGC Landran\n\n"
            displayed = set()
            for cat_name, c in matched_courses[:6]:
                if c["name"] not in displayed:
                    displayed.add(c["name"])
                    text += f"- **{c['name']}** ({c['duration']}): `{c['fee']}` — [Course Page]({c['url']})\n"
            text += f"\n*Note: Fee estimates are indicative based on official admission guidelines. Confirm exact details via official channels:*\n{_helpline()}\n\n"
            text += f"• [CGC Admissions]({LINKS['admissions']})\n• [Pay Fee Online]({LINKS['pay_fee']})"
            return _out(text, _src("admissions", "pay_fee"), ["How to apply for admission?", "Scholarship details", "Contact the admission helpline"])

        fee_breakdown_text = "### Comprehensive Course-Wise Fee Structure at CGC Landran\n\n"
        for cat_name, courses in _COURSE_FEES_CATALOG.items():
            fee_breakdown_text += f"#### {cat_name}\n"
            for c in courses:
                fee_breakdown_text += f"- **{c['name']}** ({c['duration']}): `{c['fee']}`\n"
            fee_breakdown_text += "\n"

        fee_breakdown_text += (
            f"Please confirm the latest tuition, hostel and scholarship details through the official channels:\n{_helpline()}\n\n"
            f"• [CGC Admissions]({LINKS['admissions']})\n"
            f"• [Scholarship Details]({LINKS['scholarship']})\n"
            f"• [Financial Aid]({LINKS['financial_aid']})\n"
            f"• [Pay Fee Online]({LINKS['pay_fee']})"
        )
        return _out(fee_breakdown_text, _prog_src(progs[:2]) + _src("admissions", "scholarship", "pay_fee"),
                    ["Scholarship details", "How to apply for admission?", "Contact the admission helpline"])
    
    if intent == "scholarship":
        return _out("### Scholarships and financial aid\n\nThe CGC B.Tech CSE page lists merit-based scholarships, Punjab domicile benefits, "
                    "SC/ST/OBC schemes and early-application discounts for the intake. Amounts and eligibility rules are not published "
                    f"there, so please confirm them.\n\n[Scholarship Details]({LINKS['scholarship']})\n[Financial Aid]({LINKS['financial_aid']})\n{_helpline()}",
                    _src("scholarship", "financial_aid") + _prog_src(progs[:1]), ["BBA fees", "How to apply for admission?"])

    if intent == "admissions":
        text = ("### Admissions\n\nThe official Admissions page shows a 4-step process:\n"
                "1. **Apply**: visit the website and apply\n"
                "2. **Register**: fill in details and register\n"
                "3. **Pay fee**: fill the form and pay\n"
                "4. **Upload & submit**: upload documents and submit\n\n"
                f"I could not find eligibility criteria on that page, so check the programme page or call:\n{_helpline()}\n\n"
                f"[How to Apply]({LINKS['how_to_apply']}) • [Admissions]({LINKS['admissions']})")
        if progs:
            text += "\n\n**Programme pages:**\n" + _bullets(progs[:8])
        return _out(text, _prog_src(progs[:2]) + _src("how_to_apply", "admissions"), ["Scholarship details", "Contact the admission helpline"])

    if intent == "placements":
        matched_placement_courses = []
        for cat_name, courses in _COURSE_PLACEMENTS_CATALOG.items():
            for c in courses:
                c_name_lower = c["name"].lower()
                if any(alias in q for alias in [c_name_lower, cat_name.lower()]) or any(word in q for word in tokens(c["name"])):
                    matched_placement_courses.append((cat_name, c))

        if matched_placement_courses and any(k in q for k in ["btech", "bca", "mca", "bba", "mba", "bpharm", "pharmd", "bsc", "msc", "bcom", "bhmct", "bttm", "bms", "bvoc", "engineering", "pharmacy", "computer", "business", "science", "hotel"]):
            text = "### Course-Wise Placement Highlights at CGC Landran\n\n"
            displayed = set()
            for cat_name, c in matched_placement_courses[:6]:
                if c["name"] not in displayed:
                    displayed.add(c["name"])
                    text += f"- **{c['name']}**\n  - **Highest Package:** `{c['highest_package']}`\n  - **Top Recruiters:** {c['recruiters']}\n  - [Placement Portal]({c['url']})\n\n"
            text += f"• [Official Placements Portal]({LINKS['placements']})\n• [Placement Tracker]({LINKS['placement_tracker']})"
            return _out(text, _src("placements", "placement_tracker"), ["BBA fees", "Library rules", "Contact CGC"])

        text = (
            "### Placements Breakdown by Academic Stream & Course\n\n"
            "CGC Landran has recorded **10,000+ placement offers** and **1,300+ recruiting companies**, "
            "with an overall highest package of **₹1.14 Crore PA**.\n\n"
        )
        for cat_name, courses in _COURSE_PLACEMENTS_CATALOG.items():
            text += f"#### {cat_name}\n"
            for c in courses:
                text += f"- **{c['name']}**\n  - **Highest Package:** `{c['highest_package']}`\n  - **Top Recruiters:** {c['recruiters']}\n"
            text += "\n"

        text += (
            f"• [Official Placements Portal]({LINKS['placements']})\n"
            f"• [Placement Tracker]({LINKS['placement_tracker']})"
        )
        if progs:
            text += "\n\n**Programme pages:**\n" + _bullets(progs[:6])
        return _out(text, _src("placements", "placement_tracker") + _prog_src(progs[:2]),
                    ["BBA fees", "Library rules"])

    if intent == "contact":
        primary_helplines = (
            "- **Admission Support (Toll-Free):** 1800-200-3575 (`admissions@cgc.edu.in`)\n"
            "- **Alternate Admission Lines:** +91-95921-04444, +91-95921-14444, +91-95921-24444\n"
            "- **Official WhatsApp Helpline:** +91-95922-14444\n"
            "- **General Campus Enquiry:** 0172-3984200 (`info@cgc.edu.in`)\n"
            "- **International Admissions Email:** `inadmissions@cgc.edu.in`"
        )
        
        welfare_officials = (
            "- **Campus Operations (Director General Desk):** +91-9781811111\n"
            "- **Student Affairs (Dean Student Welfare):** +91-9781925240\n"
            "- **National Anti-Ragging Helpline:** 1800-180-5522"
        )

        return _out(
            f"### Contact CGC Landran\n\n"
            f"**Address:** {CONTACT['address']}\n\n"
            f"#### Primary Helplines & Support Desks\n{primary_helplines}\n\n"
            f"#### Campus Welfare & Grievance Officials\n{welfare_officials}\n\n"
            f"[Official Contact Us page]({LINKS['contact']})",
            _src("contact"),
            ["How to apply for admission?", "BBA fees"]
        )

    if intent == "library":
        if any(kw in q for kw in ["rule", "regulation", "conduct", "fine", "penalty", "overdue", "lost book", "discipline"]):
            r = _LIBRARY_CATALOG["rules"]
            text = (
                "### Library Rules & Regulations\n\n"
                f"- **Membership Card:** {r['membership_card']}\n"
                f"- **Borrowing Policy:** {r['borrowing']}\n"
                f"- **Fines & Lost Books:** {r['fines_and_lost']}\n"
                f"- **General Conduct:** {r['conduct']}\n\n"
                f"• [Library Rules (PDF)]({LINKS['lib_rules']})\n"
                f"• [CGC Central Library Platform]({LINKS['library']})"
            )
            return _out(text, _src("lib_rules", "library"), ["Library timings", "Digital library resources", "Contact CGC"])

        if any(kw in q for kw in ["timing", "hours", "open", "closing", "schedule"]):
            r = _LIBRARY_CATALOG["rules"]
            text = (
                "### Library Timings & Operational Hours\n\n"
                f"- **Standard Schedule:** `{r['timings']}`\n\n"
                f"• [Library Rules (PDF)]({LINKS['lib_rules']})\n"
                f"• [CGC Library Portal]({LINKS['library']})"
            )
            return _out(text, _src("lib_rules", "library"), ["Library rules", "Digital library resources"])

        if any(kw in q for kw in ["digital", "e-book", "ebook", "e-journals", "database", "ieee", "delnet", "ndli", "e-resource"]):
            text = "### Digital Library Resources & Subscribed Databases\n\n"
            for d in _LIBRARY_CATALOG["digital_resources"]:
                text += f"- **{d['name']}:** {d['details']} — [Access Guide]({d['url']})\n"
            text += f"\n[Digi Library Guide (PDF)]({LINKS['lib_digi']})\n[CBS E-Libraries & Journals]({LINKS['library']})"
            return _out(text, _src("lib_digi", "library"), ["Library rules", "Library timings", "Contact CGC"])

        text = "### CGC Landran Campus Libraries & Resource Overview\n\n"
        text += "The CGC campus hosts a centralized library network featuring over **1.25 Lakh+ books**, automated via LIBSYS with CCTV security monitoring.\n\n"
        text += "#### Institute Libraries across Campus\n"
        for sec in _LIBRARY_CATALOG["sections"]:
            text += f"- **{sec['name']}**: {sec.get('volumes', '')} — [Portal]({sec['url']})\n"
        
        text += f"\n#### Key Library Facilities & Rules\n"
        text += f"- **Timings:** {_LIBRARY_CATALOG['rules']['timings']}\n"
        text += f"- **Borrowing Limits:** {_LIBRARY_CATALOG['rules']['borrowing']}\n\n"
        text += (
            f"• [Official Library Portal]({LINKS['library']})\n"
            f"• [Library Rules (PDF)]({LINKS['lib_rules']})\n"
            f"• [Digi Library Guide (PDF)]({LINKS['lib_digi']})"
        )
        return _out(text, _src("library", "lib_rules", "lib_digi"), ["Library rules", "Digital library", "Library timings"])

    if intent == "syllabus":
        use = progs or ctx_progs
        sm = _SEM.search(query)
        sem = (sm.group(1) or sm.group(2)) if sm else ctx.get("semester")
        
        if use and any(p["name"].lower().startswith("bca") for p in use) and str(sem) == "5":
            text = (
                "### BCA Semester 5: Official Syllabus & Curriculum Guide\n\n"
                "According to the verified curriculum updates for BCA Semester 5 at CGC Landran (IKGPTU framework), the subjects include:\n"
                "- **Cloud Computing (CC)**\n"
                "- **PHP Programming (Server-Side Web Technologies)**\n"
                "- **Advanced Java Programming**\n"
                "- **Internet of Things (IoT)**\n"
                "- **Minor Capstone Project**\n"
                "- **Minor Project Development (MPD)**\n\n"
                f"• [PTU Syllabus Portal]({LINKS['ptu_syllabus']})\n"
                f"• [CGC Admissions Portal]({LINKS['admissions']})"
            )
            return _out(text, _src("ptu_syllabus", "ptu") + _prog_src(use), ["BCA Semester 5 notes", "BCA fees", "BCA placements"])

        if not use:
            return _out(
                "### Official Syllabus & Curriculum Directory\n\n"
                "Please specify the programme you need the syllabus for (e.g., **B.Tech CSE**, **BCA**, **MBA**, **B.Pharm**, **B.Sc Biotech**, or **BHMCT**).\n\n"
                "#### Department-Wise Academic Curriculum Highlights:\n\n"
                "##### 1. Engineering & Technology (B.Tech / M.Tech)\n"
                "- **First Year Core (Sem 1 & 2):** Engineering Physics/Chemistry, Maths-I & II, Programming (C/Python), Electrical Basics, Graphics & Workshop.\n"
                "- **CSE / IT (Sem 3 & 4):** Data Structures & Algorithms, OOPs (C++), Digital Electronics, OS, Architecture, Discrete Maths, DBMS.\n"
                "- **ECE (Sem 3 & 4):** Network Analysis, Electronic Devices, Digital Circuit Design, Signals & Systems, Analog Circuits, Microprocessors.\n"
                "- **Mechanical (Sem 3 & 4):** Thermodynamics, Strength of Materials, Fluid Mechanics, Kinematics & Manufacturing Processes.\n"
                "- **Next-Gen AI & Specializations (Sem 5–8):** AI & ML, Deep Learning, NLP, Computer Vision, Cryptography, Blockchain, Cloud Computing, Major Capstone Project & 8th Sem Full Internship.\n"
                "- **B.Tech LEET:** Direct 2nd-year entry (Sem 3 to 8) for Engineering Diploma holders with qualifying bridge courses.\n"
                "- **M.Tech (2-Year / 4-Sem):** Research Methodology & IPR, Advanced Core/Electives, Mini-Projects, and a 2-Semester Dissertation Phase.\n\n"
                "##### 2. Computer Applications (BCA / MCA)\n"
                "- **BCA (3-Year / 6-Sem):** C/C++, Data Structures, DBMS, Web Dev, Java, Operating Systems, Mobile App Dev, Python, AI Basics, Cloud Services, Capstone Project.\n"
                "- **BCA LEET:** Direct 2nd-year entry (Sem 3 to 8) for IT/CS 3-year diploma holders.\n"
                "- **MCA (2-Year / 4-Sem):** Advanced DSA, NoSQL/SQL, Linux Shell Scripting, Cloud Ecosystems, MERN Stack, ML & AI Engines, Cyber Laws, 6-Month Corporate Internship.\n\n"
                "##### 3. Business & Commerce (BBA / B.Com / MBA)\n"
                "- **BBA & B.Com (Hons) (3-Year):** Principles of Management, Micro/Macroeconomics, Business Accounting, Taxation (GST), Company Law, Corporate Finance, Strategic Management.\n"
                "- **MBA General (2-Year):** Management Foundations, Business Analytics, Corporate Finance, Human Resources, Production Operations, Dual Specializations (Marketing, HR, Finance, MIS).\n"
                "- **MBA Digital Marketing (2-Year):** SEO Tools, Content Strategy, Web Analytics, Meta & Google Paid Ads, SMM, CRM Integration, Digital Brand Valuation.\n\n"
                "##### 4. Pharmacy (B.Pharm / Pharm.D / M.Pharm)\n"
                "- **B.Pharm (4-Year / 8-Sem):** Anatomy & Physiology, Pharmaceutics, Organic/Medicinal Chemistry, Pharmacology, Pharmacognosy, Biopharmaceutics, Jurisprudence, Instrumental Analysis, Project Work.\n"
                "- **Pharm.D (6-Year Clinical):** Annual mode structure covering Pathophysiology, Clinical Pharmacy, Pharmacotherapeutics I–III, Toxicology, Hospital Clerkship (Yr 5), and 12-Month Internship Residency (Yr 6).\n"
                "- **Pharm.D Post Baccalaureate:** 3-Year clinical track for B.Pharm graduates.\n"
                "- **M.Pharm (2-Year):** Advanced Core Research, Analytical Techniques, Biostatistics, Thesis Defense.\n\n"
                "##### 5. Science & Biotechnology (B.Sc / M.Sc)\n"
                "- **B.Sc. Biotechnology (3-Year):** Cell Biology, Genetics, Immunology, Genetic Engineering, Tissue Culture, Bioprocess Engineering.\n"
                "- **M.Sc. Biotechnology (2-Year):** Molecular Genetics, Immunotechnology, Enzymology, Genomics & Proteomics, Research Bench-Work Dissertation.\n"
                "- **Specialized B.Sc Tracks:** B.Sc AI & ML, B.Sc Multimedia, B.Sc Graphics & Web Designing, B.Sc (Hons.) Nutrition & Dietetics.\n\n"
                "##### 6. Hotel Management & Tourism (BHMCT / BTTM / BMS / B.Voc)\n"
                "- **BHMCT (4-Year):** Food Production, F&B Service, Front Office, Housekeeping, Hotel Accounting, 6-Month 5-Star Hotel Industrial Training, Culinary Management.\n"
                "- **BTTM / BMS / B.Voc:** Tourism Geography, Ticketing, Travel Operations, Aviation Cargo & Passenger Handling, Skilled Vocational Shift Work.\n\n"
                f"You can also browse complete scheme PDFs directly on the [PTU Syllabus Portal]({LINKS['ptu_syllabus']}).",
                _src("find_program", "ptu_syllabus"),
                ["B.Tech CSE syllabus", "BCA syllabus", "MBA syllabus", "B.Pharm syllabus"],
                False
            )

        if len(use) > 1:
            return _out(
                "### Multiple Programmes Found\n\n"
                "Which programme do you mean?\n" + _bullets(use[:10]) +
                "\n\nPlease specify the exact programme and semester (e.g., *BCA Semester 5* or *B.Tech CSE Semester 3*) to view its detailed curriculum breakdown.",
                _src("ptu_syllabus"),
                [p["name"] + " syllabus" for p in use[:3]],
                False
            )

        p = use[0]
        label = p["name"] + (f" Semester {sem}" if sem else "")
        text = (
            f"### {label}: Official Syllabus & Curriculum Guide\n\n"
            f"The official curriculum and scheme documents for **{p['name']}** are governed by IKGPTU / CGC Autonomous frameworks.\n\n"
            f"**How to download your official scheme PDF:**\n"
            f"1. Visit the official [PTU Syllabus Portal]({LINKS['ptu_syllabus']}).\n"
            f"2. Select **{p['name']}** under your respective department.\n"
            "3. Choose the **Scheme / Batch Year** matching your admission session.\n"
            f"4. Access the syllabus PDF for **Semester {sem if sem else '[Your Semester]'}**.\n\n"
            f"• **CGC Programme Page:** [{p['name']} Overview]({p['url']})\n"
            f"• **IKGPTU Main Website:** [{LINKS['ptu']}]({LINKS['ptu']})\n\n"
            f"*Note: For autonomous or specialized certification modules, please verify with your department office or call the helpline at **{CONTACT['toll_free']}**.*"
        )

        from backend.chat_engine import ptu_lookup, schemes_text
        text += schemes_text(ptu_lookup(p["name"]))

        for d in (kb_docs or []):
            c = (ctx.get("course") or "").lower()
            if d.get("category") == "academic_syllabus" and c and c in f"{d.get('title','')} {d.get('content','')}".lower() \
                    and (not sem or f"sem {sem}" in d["content"].lower() or f"semester {sem}" in d["content"].lower()):
                text += f"\n\n**Project knowledge-base entry (not re-checked against the PTU PDF):**\n{d['content']}"
                break

        return _out(
            text,
            _src("ptu_syllabus", "ptu") + _prog_src([p]),
            [f"Notes for a {p['name']} subject", f"{p['name']} fees", f"{p['name']} placements"]
        )

    if intent == "exam":
        exam_pattern = (
            "#### Standard Mid-Semester Exam (MST) Pattern at CGC Landran\n"
            "Most departments (CEC, CBSA, CCT, CCP) follow a structured internal assessment strategy before the final university examinations:\n\n"
            "- **Mid-Semester Tests (MST 1 & 2):** Written internal exams conducted twice a semester to evaluate 40% of the total internal grading system.\n"
            "- **Evaluation Structure:** Splits questions into foundational definitions, short application problems, and long-form comprehensive analytical answers.\n"
            "- **Practical Lab Exams:** Includes direct laboratory viva-voce assessments, file records check, and experiment executions just prior to theory exam dates."
        )
        
        text = (
            "### Exams, Evaluation & Results\n\n"
            "I do not have direct access to private student records, individual marks, attendance percentages, or personalized admit cards.\n\n"
            f"{exam_pattern}\n\n"
            "#### Official Examination Portals & Links:\n"
            "- **IKGPTU Exam Portal (Results, Admit Cards & Date Sheets):** [https://www.ptuexam.com/](https://www.ptuexam.com/)\n"
            f"- **IKGPTU Main Site:** [{LINKS['ptu']}]({LINKS['ptu']})\n"
            f"- **CGC Examination Evaluation Rules:** [Examination Evaluation]({LINKS['exam_eval']})\n\n"
            f"For individual record queries, re-appear forms, or date sheet clarifications, contact your department office or call **{CONTACT['toll_free']}**."
        )

        return _out(
            text,
            _src("ptu", "exam_eval"),
            ["BCA syllabus", "Contact CGC"]
        )

    if intent == "campus":
        campus_highlights = (
            "The CGC Landran Campus is a modern, **40+ acre tech-driven campus** located in Mohali, Punjab.\n\n"
            "#### Core Campus Infrastructure & Facilities:\n"
            "- **Academic Blocks:** Dedicated blocks for each department, smart classrooms, and 24/7 high-speed computer labs.\n"
            "- **Accommodation:** Separate multi-story boys' and girls' hostels with Wi-Fi, laundry facilities, and a vegetarian mess.\n"
            "- **Food & Hangouts:** Large central student canteens alongside on-campus **Subway** and **Cafe Coffee Day (CCD)** outlets.\n"
            "- **Sports & Fitness:** Dedicated Cricket/Football grounds, Basketball courts, and separate gyms for boys and girls.\n"
            "- **Utilities & Safety:** 24/7 medical dispensary, on-campus bank branch, multiple ATMs, and a regular bus shuttle network."
        )

        text = (
            f"### Campus, Hostel & Infrastructure\n\n"
            f"{campus_highlights}\n\n"
            f"#### Official Campus Links & Enquiries:\n"
            f"• [360° Virtual Campus Tour]({LINKS['tour']})\n"
            f"• [College Rules & Regulations]({LINKS['rules']})\n\n"
            f"For hostel fee breakdowns, room seat allocation, or specific transport route queries, please contact:\n{_helpline()}"
        )

        return _out(
            text,
            _src("tour", "rules", "contact"),
            ["Library rules", "Contact CGC"]
        )

    if intent == "about":
        return _out("### About CGC Landran\n\nChandigarh Group of Colleges, Landran (Mohali, Punjab) was established in 2001 and offers **55+ UG and PG programmes**. "
                    "The Admissions page states NAAC A+ accreditation, and lists NBA recognition for CSE programmes, QS I-GAUGE Platinum and NIRF/other rankings. "
                    f"Approvals and affiliations are on their own page.\n\n[Overview]({LINKS['overview']})\n[Approval & Affiliation]({LINKS['approvals']})\n[Awards & Rankings]({LINKS['rankings']})",
                    _src("overview", "approvals", "rankings"), ["Courses offered", "Placements", "Contact CGC"])

    if intent == "programs":
        matched_catalog_courses = []
        for cat in _EXHAUSTIVE_PROGRAM_CATALOG:
            for c in cat["courses"]:
                c_name_lower = c["name"].lower()
                if any(alias in q for alias in [c_name_lower, cat["category_name"].lower()]) or any(word in q for word in tokens(c["name"])):
                    matched_catalog_courses.append((cat["category_name"], c))

        if matched_catalog_courses and any(k in q for k in ["btech", "bca", "mca", "bba", "mba", "bpharm", "pharmd", "mcom", "dpharm", "bsc", "msc", "bcom", "bhmct", "bttm", "b.sc", "engineering", "pharmacy", "computer", "business", "science", "hotel", "multimedia"]):
            text = "### Exhaustive Programme & Course Directory at CGC Landran\n\n"
            displayed = set()
            for cat_name, c in matched_catalog_courses[:8]:
                if c["name"] not in displayed:
                    displayed.add(c["name"])
                    text += f"- **{c['name']}** ({c.get('level', 'N/A')} — {c.get('duration', 'N/A')})\n  - [Official Programme Page]({c['url']})\n\n"
            text += f"• [Find your Program]({LINKS['find_program']})\n• [CGC Landran Home]({LINKS['home']})"
            return _out(text, _src("find_program", "home"), ["BCA fees", "MBA syllabus", "B.Tech CSE placements"])

        text = (
            "### Exhaustive Programme & Course Directory at CGC Landran\n\n"
            "Chandigarh Group of Colleges (CGC) Landran offers more than 50+ undergraduate (UG), postgraduate (PG), diploma, and lateral entry (LEET) programs. "
            "These programs are distributed across its targeted constituent colleges (Engineering, Management, Pharmacy, Computer Applications, Biotechnology, and Hotel Management)[cite: 1].\n\n"
        )
        for cat in _EXHAUSTIVE_PROGRAM_CATALOG:
            text += f"#### {cat['category_name']}\n"
            text += f"*{cat['description']}*\n"
            for c in cat["courses"]:
                text += f"- **{c['name']}** ({c.get('level', 'N/A')} — {c.get('duration', 'N/A')}): [Page]({c['url']})\n"
            text += "\n"

        text += f"For detailed course specifications, explore [Find your Program]({LINKS['find_program']}) or call **{CONTACT['toll_free']}**."

        return _out(
            text,
            _src("find_program", "home"),
            ["BCA fees", "MBA syllabus", "B.Tech CSE placements", "B.Pharm fees"]
        )
    return None


def fallback_unknown() -> Dict:
    return _out("Sorry, I couldn't understand that question. You can ask me about **CGC Landran**, **PTU**, **Library**, **Courses**, **Academics**, "
                "**Syllabus**, **Notes**, **Important Questions**, or **Quizzes**.",
                _src("home", "contact"), ["Where is the library?", "BCA 5th semester subjects", "What courses are available?", "PTU examination information"], False)


def fallback_ai_unavailable() -> Dict:
    result = fallback_unknown()
    result["answer"] += "\n\n*Explaining general study topics needs an AI key on the server.*"
    return result