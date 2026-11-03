from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import re
import httpx

from backend.config import settings

router = APIRouter(prefix="/api/academic", tags=["Academic"])

# --- Request Models ---

class QuizRequest(BaseModel):
    subject: str
    course: Optional[str] = None
    semester: Optional[int] = None
    count: Optional[int] = 5

class NoteRequest(BaseModel):
    subject: str
    course: Optional[str] = None
    semester: Optional[int] = None
    topic: Optional[str] = None

# --- AI System Prompts ---

QUIZ_SYSTEM = """You are an expert academic professor. Generate multiple-choice quiz questions in JSON format for the requested subject and programme.
Return a JSON object with a key "questions" containing a list of objects, where each object has:
- "question": string
- "options": list of 4 strings
- "correct_index": integer (0 to 3)
- "explanation": string explaining the correct answer"""

NOTE_SYSTEM = """You are an expert academic tutor. Generate comprehensive, well-structured study notes in JSON format for the requested subject and topic.
Return a JSON object with:
- "subject": string
- "topic": string
- "overview": brief introductory summary string
- "key_points": list of strings detailing essential concepts
- "examples": list of strings or code snippets illustrating the concepts
- "summary": concluding takeaway string"""

# --- Reference Websites ---

_REFERENCE_WEBSITES = [
    {"name": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org", "description": "Comprehensive tutorials on programming, DSA, and computer science subjects."},
    {"name": "TutorialsPoint", "url": "https://www.tutorialspoint.com", "description": "Free tutorials spanning programming, databases, engineering, management, and science."},
    {"name": "PrepNotez", "url": "https://www.prepnotez.com", "description": "Free academic notes platform covering engineering and pharmacy subjects across all semesters."},
    {"name": "BrainKart", "url": "https://www.brainkart.com", "description": "Online study material and lecture notes for pharmacy, engineering, and management."}
]

# --- Comprehensive Subject Aliases for CGC Courses ---

_ALIASES = {
    # Computer Applications & IT (BCA / B.Tech)
    "operating systems": "os",
    "operating system": "os",
    "server-side web technologies (php)": "php",
    "server-side web technologies": "php",
    "php programming": "php",
    "data structures and algorithms": "dsa",
    "data structures": "dsa",
    "database management systems": "dbms",
    "database management": "dbms",
    "computer networks": "networks",
    "computer network": "networks",
    "software engineering": "se",
    "object oriented programming": "c++",
    "java programming": "java",
    "python programming": "python",
    
    # Management & Commerce (MBA / BBA / B.Com)
    "principles of management": "management",
    "management principles": "management",
    "financial accounting": "accounting",
    "marketing management": "marketing",
    "human resource management": "hrm",
    "business economics": "economics",
    
    # Pharmacy (B.Pharm)
    "pharmacokinetics": "pharmacy",
    "pharmacodynamics": "pharmacy",
    "pharmaceutics": "pharmaceutics",
    "pharmacognosy": "pharmacy",
    "human anatomy and physiology": "pharmacy",
    
    # Biotechnology & Electronics
    "biotechnology": "biotechnology",
    "recombinant dna technology": "biotechnology",
    "basic electronics": "electronics",
    "thermodynamics": "thermodynamics"
}

# --- Expanded Curated Quiz Question Banks ---

_CURATED = {
    "c++": [
        {"question": "What is the size of a standard integer in C++ on a 32-bit system?", "options": ["2 bytes", "4 bytes", "8 bytes", "1 byte"], "correct_index": 1, "explanation": "A standard int is typically 4 bytes (32 bits) on modern architectures."},
        {"question": "Which of the following is used to handle exceptions in C++?", "options": ["try, catch, throw", "try, except, raise", "handle, error, throw", "attempt, rescue, fail"], "correct_index": 0, "explanation": "C++ uses try, catch, and throw blocks for structured exception handling."},
        {"question": "What is a pure virtual function?", "options": ["A function with no return type", "A member function that must be overridden in derived classes", "A function that cannot be called under any circumstances", "A private helper function"], "correct_index": 1, "explanation": "Pure virtual functions (= 0) make a class abstract and enforce implementation in subclasses."},
        {"question": "Which C++ feature allows functions to have the same name with different parameters?", "options": ["Function overriding", "Function overloading", "Operator overloading", "Virtual functions"], "correct_index": 1, "explanation": "Function overloading enables multiple functions with identical names but distinct parameter signatures."},
        {"question": "What is the correct syntax to output 'Hello' to the console in C++?", "options": ["print('Hello');", "cout << 'Hello';", "Console.WriteLine('Hello');", "printf('Hello');"], "correct_index": 1, "explanation": "std::cout combined with the insertion operator << is standard for C++ console output."}
    ],
    "dsa": [
        {"question": "What is the worst-case time complexity of QuickSort?", "options": ["O(n log n)", "O(n)", "O(n^2)", "O(log n)"], "correct_index": 2, "explanation": "QuickSort degrades to O(n^2) when poor pivot selections occur."},
        {"question": "Which data structure operates on a First-In-First-Out (FIFO) basis?", "options": ["Stack", "Queue", "Tree", "Graph"], "correct_index": 1, "explanation": "Queues process elements in FIFO order."},
        {"question": "What is the time complexity of searching an element in a balanced Binary Search Tree (BST)?", "options": ["O(n)", "O(1)", "O(log n)", "O(n log n)"], "correct_index": 2, "explanation": "Balanced BST searches halve the search space at each step, taking O(log n)."},
        {"question": "Which traversal technique visits the root node first, then left subtree, then right subtree?", "options": ["Inorder", "Preorder", "Postorder", "Level order"], "correct_index": 1, "explanation": "Preorder traversal follows Root -> Left -> Right."},
        {"question": "What is the primary advantage of a hash table?", "options": ["Ordered data storage", "Constant time O(1) average case lookups, insertions, and deletions", "Zero memory overhead", "Self-balancing tree properties"], "correct_index": 1, "explanation": "Hash tables provide rapid average-case O(1) time complexity operations."}
    ],
    "dbms": [
        {"question": "What does ACID stand for in database management systems?", "options": ["Atomicity, Consistency, Isolation, Durability", "Access, Control, Index, Data", "Association, Consistency, Integration, Dictionary", "Atomicity, Concurrency, Independence, Distribution"], "correct_index": 0, "explanation": "ACID properties guarantee reliable transaction processing in RDBMS."},
        {"question": "Which normal form removes transitive dependencies?", "options": ["First Normal Form (1NF)", "Second Normal Form (2NF)", "Third Normal Form (3NF)", "Boyce-Codd Normal Form (BCNF)"], "correct_index": 2, "explanation": "3NF requires that all non-key attributes are functionally dependent only on the primary key."},
        {"question": "What is a primary key?", "options": ["Any column in a table", "A unique identifier for each record in a table that cannot be null", "A foreign table reference", "A password hash"], "correct_index": 1, "explanation": "Primary keys uniquely identify table tuples and forbid null values."},
        {"question": "What is SQL used for?", "options": ["Styling web pages", "Managing and querying relational databases", "Operating system kernel compilation", "Network packet routing"], "correct_index": 1, "explanation": "Structured Query Language (SQL) is the standard language for database manipulation."},
        {"question": "What is a foreign key?", "options": ["A key used to encrypt database backups", "A field linking two tables together to establish a relationship", "A primary key from another database server", "An index on a remote server"], "correct_index": 1, "explanation": "Foreign keys enforce referential integrity between tables."}
    ],
    "os": [
        {"question": "What is the primary role of an operating system?", "options": ["Compiling high-level programming languages", "Managing hardware resources and providing a user interface", "Designing graphical web pages", "Executing virus scans"], "correct_index": 1, "explanation": "The OS acts as an intermediary between computer hardware and user applications."},
        {"question": "What is virtual memory?", "options": ["RAM installed on graphics cards", "A memory management technique that uses secondary storage as an extension of RAM", "Cache memory inside the CPU", "Cloud backup storage"], "correct_index": 1, "explanation": "Virtual memory maps virtual addresses to physical memory and disk space."},
        {"question": "What is a process in an operating system?", "options": ["A program in execution", "A hardware component", "A static file stored on a hard drive", "An idle background thread"], "correct_index": 0, "explanation": "A process represents an active instance of a running program."},
        {"question": "Which CPU scheduling algorithm gives CPU time to processes in a cyclic order using a time quantum?", "options": ["First-Come, First-Served (FCFS)", "Shortest Job First (SJF)", "Round Robin", "Priority Scheduling"], "correct_index": 2, "explanation": "Round Robin assigns fixed time slices (quanta) to processes fairly."},
        {"question": "What is thrashing?", "options": ["CPU running at maximum overclocked speed", "A condition where the system spends most of its time swapping pages in and out of memory", "Hard drive defragmentation", "Network packet collision"], "correct_index": 1, "explanation": "Thrashing severely degrades performance due to excessive page faulting."}
    ],
    "networks": [
        {"question": "Which layer of the OSI model is responsible for routing packets across multiple networks?", "options": ["Physical Layer", "Data Link Layer", "Network Layer", "Transport Layer"], "correct_index": 2, "explanation": "The Network layer (Layer 3) handles packet routing and logical addressing (e.g., IP)."},
        {"question": "What protocol is used to reliably transfer web pages on the internet?", "options": ["FTP", "SMTP", "HTTP/HTTPS", "SNMP"], "correct_index": 2, "explanation": "Hypertext Transfer Protocol (HTTP/HTTPS) governs web browser communication."},
        {"question": "What device operates at the Data Link Layer and filters traffic using MAC addresses?", "options": ["Hub", "Repeater", "Switch", "Router"], "correct_index": 2, "explanation": "Network switches forward frames using physical MAC addresses."}
    ],
    "management": [
        {"question": "Which management function involves establishing goals and determining actions in advance?", "options": ["Organizing", "Planning", "Staffing", "Controlling"], "correct_index": 1, "explanation": "Planning sets objectives and maps out strategic routes to achieve them."},
        {"question": "Who proposed the 14 Principles of Management?", "options": ["F.W. Taylor", "Henri Fayol", "Max Weber", "Peter Drucker"], "correct_index": 1, "explanation": "Henri Fayol formulated classical administrative management principles."},
        {"question": "What does SWOT analysis evaluate?", "options": ["Sales, Workforce, Operations, Technology", "Strengths, Weaknesses, Opportunities, Threats", "Suppliers, Workers, Owners, Taxpayers", "Systems, Workflow, Output, Time"], "correct_index": 1, "explanation": "SWOT evaluates internal and external strategic factors."}
    ],
    "accounting": [
        {"question": "What is the primary equation of double-entry accounting?", "options": ["Assets = Liabilities + Equity", "Assets = Income - Expenses", "Revenue = Sales - Cost", "Liabilities = Assets + Equity"], "correct_index": 0, "explanation": "Assets must always equal Liabilities plus Owner's Equity."},
        {"question": "Which financial statement reports revenues and expenses over a specific period?", "options": ["Balance Sheet", "Income Statement (Profit & Loss)", "Cash Flow Statement", "Statement of Retained Earnings"], "correct_index": 1, "explanation": "Income statements measure profitability."},
        {"question": "What does a debit entry do in an asset account?", "options": ["Decreases the asset", "Increases the asset", "Has no effect", "Closes the account"], "correct_index": 1, "explanation": "Debits increase asset and expense accounts."}
    ],
    "pharmacy": [
        {"question": "What does 'Pharmacokinetics' study?", "options": ["What the drug does to the body", "What the body does to the drug (ADME)", "Drug pricing dynamics", "Plant extractions"], "correct_index": 1, "explanation": "Pharmacokinetics analyzes Absorption, Distribution, Metabolism, and Excretion."},
        {"question": "What is 'Pharmacodynamics'?", "options": ["Drug manufacturing processes", "Study of biochemical and physiological effects of drugs on the body", "Drug transportation logistics", "Clinical trial statistics"], "correct_index": 1, "explanation": "Pharmacodynamics evaluates drug mechanisms of action and receptor interactions."},
        {"question": "Which regulatory body governs pharmacy education and practice in India?", "options": ["PCI (Pharmacy Council of India)", "AICTE", "UGC", "ICMR"], "correct_index": 0, "explanation": "The Pharmacy Council of India regulates pharmacy standards and curricula."}
    ]
}

# --- Expanded Curated Study Notes Banks ---

_CURATED_NOTES = {
    "dsa": {
        "subject": "Data Structures and Algorithms",
        "topic": "Arrays, Linked Lists & Trees",
        "overview": "DSA provides the foundational computational techniques for organizing data efficiently in memory.",
        "key_points": [
            "Arrays offer O(1) random indexing but rigid static allocation.",
            "Linked lists permit dynamic node insertion and deletion with O(n) traversal.",
            "Binary search trees maintain sorted hierarchies enabling O(log n) searches.",
            "Graph traversal algorithms include Breadth-First Search (BFS) and Depth-First Search (DFS)."
        ],
        "examples": ["std::vector dynamic array resizing", "Recursive tree inorder traversal"],
        "summary": "Selecting optimal data structures minimizes execution time and memory overhead."
    },
    "os": {
        "subject": "Operating Systems",
        "topic": "Processes, Threads & Memory Management",
        "overview": "Operating systems manage hardware abstraction, process scheduling, and virtual memory allocation.",
        "key_points": [
            "Processes are active instances of programs executing in their own address spaces.",
            "Virtual memory expands available RAM using secondary storage paging.",
            "CPU scheduling algorithms optimize processor utilization and turnaround times.",
            "Synchronization mechanisms like semaphores prevent race conditions."
        ],
        "examples": ["Round Robin scheduling queues", "Mutex lock acquisition and release"],
        "summary": "Operating systems ensure efficient, secure multi-tasking resource allocation."
    },
    "dbms": {
        "subject": "Database Management Systems",
        "topic": "Relational Model & Normalization",
        "overview": "DBMS ensures structured, persistent, and secure storage of application data with ACID compliance.",
        "key_points": [
            "ACID properties guarantee robust transaction handling.",
            "Normalization (1NF, 2NF, 3NF, BCNF) reduces data redundancy and prevents anomalies.",
            "Primary and foreign keys establish referential table integrity.",
            "Indexes accelerate query retrieval speeds."
        ],
        "examples": ["SQL SELECT JOIN queries", "Third Normal Form elimination"],
        "summary": "Proper database design and indexing maximize performance and protect data integrity."
    },
    "networks": {
        "subject": "Computer Networks",
        "topic": "OSI Layers & Routing Protocols",
        "overview": "Computer networks enable seamless communication and data interchange across distributed nodes.",
        "key_points": [
            "The OSI 7-layer model standardizes network communication protocols.",
            "IP addressing and routing handle packet delivery across subnets.",
            "TCP ensures reliable connection-oriented delivery; UDP offers fast connectionless transmission.",
            "DNS translates human-readable domain names to IP addresses."
        ],
        "examples": ["TCP three-way handshake", "IPv4 subnet masking"],
        "summary": "Understanding network protocols is crucial for distributed and web application architecture."
    },
    "php": {
        "subject": "Server-Side Web Technologies (PHP)",
        "topic": "PDO Database Connectivity & Sessions",
        "overview": "PHP is a powerful server-side scripting language for building dynamic web applications.",
        "key_points": [
            "PHP Data Objects (PDO) provides a secure, database-agnostic interface for querying databases.",
            "Prepared statements protect applications against SQL injection vulnerabilities.",
            "Sessions (`session_start()`) securely store user state data across multiple HTTP requests.",
            "Superglobal arrays like `$_POST` and `$_GET` handle incoming HTTP client parameters."
        ],
        "examples": ["$pdo = new PDO(...);", "session_start();"],
        "summary": "Mastering PDO and session handling is critical for building secure web applications."
    },
    "management": {
        "subject": "Principles of Management",
        "topic": "Planning, Organizing & Leadership",
        "overview": "Management science outlines how organizations coordinate resources efficiently to achieve strategic goals.",
        "key_points": [
            "Core functions include Planning, Organizing, Staffing, Directing, and Controlling.",
            "Henri Fayol formulated 14 classic administrative management principles.",
            "SWOT analysis evaluates internal and external business factors.",
            "Delegation of authority empowers lower tiers while maintaining governance."
        ],
        "examples": ["SMART goal setting", "Organizational hierarchy charts"],
        "summary": "Effective management aligns team workflows with long-term enterprise strategy."
    },
    "accounting": {
        "subject": "Financial Accounting",
        "topic": "Double-Entry Bookkeeping & Statements",
        "overview": "Accounting records, classifies, and summarizes monetary transactions to report financial health.",
        "key_points": [
            "Fundamental accounting equation: Assets = Liabilities + Owner's Equity.",
            "Income statements measure operational profitability over a period.",
            "Balance sheets report assets, liabilities, and equity at a specific point in time.",
            "Debits increase asset/expense accounts and credits increase liability/equity accounts."
        ],
        "examples": ["Trial balance verification", "Depreciation journal entries"],
        "summary": "Accurate financial accounting is mandatory for regulatory compliance and stakeholder transparency."
    },
    "pharmacy": {
        "subject": "Pharmacy & Pharmacology",
        "topic": "Pharmacokinetics & Pharmacodynamics",
        "overview": "Pharmacology studies drug action, interaction, and the biological effects of pharmaceutical compounds.",
        "key_points": [
            "Pharmacokinetics covers ADME: Absorption, Distribution, Metabolism, and Excretion.",
            "Pharmacodynamics evaluates drug mechanisms of action at receptor sites.",
            "Agonists trigger biological responses; antagonists block them.",
            "Half-life ($t_{1/2}$) measures the time required for plasma concentration to halve."
        ],
        "examples": ["Hepatic first-pass metabolism", "Competitive receptor antagonism"],
        "summary": "Pharmacology bridges chemical drug structures with safe and effective clinical patient treatments."
    }
}

# --- Helper Functions (Defined before routes) ---

def llm_complete(system: str, user: str, json_mode: bool = False, max_tokens: int = 1200) -> Optional[str]:
    """One OpenAI-compatible chat call. Returns None when no key is set or the call fails."""
    if not settings.OPENAI_API_KEY:
        return None
    body = {
        "model": settings.AI_MODEL, 
        "temperature": 0.3, 
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        with httpx.Client(timeout=40.0) as client:
            r = client.post(
                f"{settings.AI_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}, 
                json=body
            )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None

def _get_matched_key(subject: str) -> str:
    cleaned = subject.strip().lower()
    if cleaned in _ALIASES:
        return _ALIASES[cleaned]
    for key in _CURATED:
        if key in cleaned or cleaned in key:
            return key
    return cleaned

def _clean_questions(raw):
    out = []
    for q in raw or []:
        o = q.get("options") if isinstance(q, dict) else None
        i = q.get("correct_index") if isinstance(q, dict) else None
        if isinstance(o, list) and len(o) == 4 and isinstance(i, int) and 0 <= i < 4 and isinstance(q.get("question"), str):
            out.append({
                "question": q["question"][:400], 
                "options": [str(x)[:200] for x in o], 
                "correct_index": i,
                "explanation": str(q.get("explanation", ""))[:500]
            })
    return out

# --- API Endpoints ---

@router.get("/syllabus")
def get_syllabus(course: str = Query(..., description="Course name such as BCA, MBA or B.Tech"),
                 semester: Optional[str] = Query(None),
                 subject: Optional[str] = Query(None)):
    """Return syllabus results for a course and semester with a deterministic fallback."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    with open(os.path.join(data_dir, "academic.json"), "r", encoding="utf-8") as fh:
        academic = json.load(fh)

    courses = academic.get("courses", {})
    course_key = None
    requested = (course or "").strip().lower()
    for key, info in courses.items():
        aliases = {key.lower()}
        aliases.update(a.lower() for a in info.get("aliases", []))
        if requested in aliases or requested in key.lower():
            course_key = key
            break

    if course_key is None:
        for key in courses:
            if requested.startswith(key.lower()):
                course_key = key
                break

    if course_key is None:
        if "pharm" in requested:
            course_key = "B.Pharm"
        elif "mba" in requested:
            course_key = "MBA"
        elif "mca" in requested:
            course_key = "MCA"
        elif "bca" in requested:
            course_key = "BCA"
        elif "btech" in requested or "engineering" in requested:
            course_key = "B.Tech"
        elif "bba" in requested:
            course_key = "BBA"
        else:
            course_key = course.strip() or "BCA"

    course_info = courses.get(course_key, {})
    semesters = course_info.get("semesters", {})
    sem_key = str(semester) if semester and str(semester).isdigit() else next(iter(semesters), "1")
    subjects = semesters.get(sem_key, {}).get("subjects", [])
    if not subjects and semesters:
        for key in sorted(semesters, key=lambda s: int(s) if s.isdigit() else 99):
            if semesters[key].get("subjects"):
                subjects = semesters[key]["subjects"]
                sem_key = key
                break

    results = []
    for subj in subjects:
        title = f"{course_key} Semester {sem_key}: {subj.get('name', 'Subject')}"
        notes = subj.get("notes") or []
        syllabus = subj.get("syllabus") or []
        summary = "\n".join(
            f"- {item.get('unit', 'Unit')}: {item.get('topics', item.get('title', ''))}"
            for item in syllabus[:3]
        ) or (notes[0].get("explanation", "") if notes else "Official PTU curriculum references")
        results.append({
            "title": title,
            "course": course_key,
            "semester": sem_key,
            "subject": subj.get("name"),
            "content": summary,
            "source": course_info.get("source") or "ptu_official_syllabus_2026_onwards",
        })

    if not results:
        results.append({
            "title": f"{course_key} Semester {sem_key} curriculum",
            "course": course_key,
            "semester": sem_key,
            "subject": subject or "General syllabus",
            "content": f"Official PTU curriculum information for {course_key} Semester {sem_key} is available on the PTU syllabus portal.",
            "source": course_info.get("source") or "ptu_official_syllabus_2026_onwards",
        })

    resources = [{
        "title": f"{course_key} syllabus portal",
        "url": f"https://ptu.ac.in/syllabus/{course_key.lower().replace('.', '').replace(' ', '-') if course_key else 'course'}",
        "source_title": "PTU",
    }]
    if course_key.lower() == "bca":
        resources.append({
            "title": "BCA syllabus (official PTU PDF)",
            "url": "https://ptu.ac.in/syllabus/bca",
            "source_title": "Official",
        })
    if "pharm" in course_key.lower():
        resources[0]["url"] = "https://ptu.ac.in/syllabus/pharmacy"
    elif "mba" in course_key.lower():
        resources[0]["url"] = "https://ptu.ac.in/syllabus/mba"
    elif "bca" in course_key.lower():
        resources[0]["url"] = "https://ptu.ac.in/syllabus/bca"
    elif "b.tech" in course_key.lower() or "b_tech" in course_key.lower() or "btech" in course_key.lower():
        resources[0]["url"] = "https://ptu.ac.in/syllabus/btech"

    return {"course": course_key, "semester": sem_key, "count": len(results), "results": results, "resources": resources}

@router.post("/quiz")
def generate_quiz(req: QuizRequest):
    """Quiz generator for any subject with safe AI primary execution and comprehensive CGC curated fallback."""
    subject, n = req.subject.strip(), max(1, min(req.count or 5, 10))
    where = " ".join(x for x in [req.course, f"Semester {req.semester}" if req.semester else ""] if x)
    
    try:
        text = llm_complete(QUIZ_SYSTEM, f"Subject: {subject}\nProgramme: {where or 'not specified'}\nNumber of questions: {n}", json_mode=True)
        if text:
            data = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text))
            qs = _clean_questions(data.get("questions") if isinstance(data, dict) else data)
            if qs:
                return {"subject": subject, "course": req.course, "questions": qs[:n], "ai": True}
    except Exception:
        pass
            
    match_key = _get_matched_key(subject)
    bank = _CURATED.get(match_key, _CURATED.get("dsa", []))
    
    if not settings.OPENAI_API_KEY and not bank:
        return {"subject": subject, "course": req.course, "questions": [], "message": "An AI key is required to generate fresh quiz questions for this subject."}
    
    return {"subject": subject, "course": req.course, "questions": bank[:n], "ai": False}

@router.post("/notes")
def generate_notes(req: NoteRequest):
    """Study notes generator with AI primary execution and comprehensive CGC curated offline fallback."""
    subject, topic = req.subject.strip(), (req.topic or "").strip()
    where = " ".join(x for x in [req.course, f"Semester {req.semester}" if req.semester else ""] if x)
    
    try:
        prompt = f"Subject: {subject}\nTopic: {topic or 'General Overview'}\nProgramme: {where or 'not specified'}"
        text = llm_complete(NOTE_SYSTEM, prompt, json_mode=True)
        if text:
            data = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text))
            if isinstance(data, dict) and data.get("key_points"):
                return {"subject": subject, "topic": topic, "notes": data, "ai": True, "reference_websites": _REFERENCE_WEBSITES}
    except Exception:
        pass
            
    match_key = _get_matched_key(subject)
    note_data = _CURATED_NOTES.get(match_key, {
        "subject": subject,
        "topic": topic or "Core Overview",
        "overview": f"Comprehensive curriculum summary notes for {subject}.",
        "key_points": [
            "Core fundamental concepts and architectural definitions.",
            "Standard operational methodologies and industry best practices.",
            "Practical problem-solving approaches and implementation examples."
        ],
        "examples": ["Refer to official prescribed textbooks and department lecture slides."],
        "summary": "Review foundational concepts regularly and practice sample problem statements."
    })
    
    return {"subject": subject, "topic": topic, "notes": note_data, "ai": False, "reference_websites": _REFERENCE_WEBSITES}