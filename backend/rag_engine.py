import re
import json
import math
from typing import Dict, List, Optional, Tuple
from backend.database import get_db_connection

# Common intent keywords
INTENT_PATTERNS = {
    "departments_colleges": [
        r"\bdepartments?\b", r"\bdepartment\s*names?\b", r"\bnames?\s+of\s+departments?\b",
        r"\blist\s+of\s+departments?\b", r"\ball\s+departments?\b", r"\bcolleges?\b",
        r"\binstitutes?\b", r"\bfacult(?:y|ies)\b", r"\bschools?\b", r"\bbranches\b",
        r"\bcec\b", r"\bcbsa\b", r"\bccp\b", r"\bcch\b", r"\bdca\b",
        r"\bwhich\s+departments?\b", r"\bwhat\s+departments?\b"
    ],
    "library_resources": [
        r"\blibrary\b", r"\bbook\b", r"\bbooks\b", r"\be-book\b", r"\bjournal\b",
        r"\bndli\b", r"\bdelnet\b", r"\bieee\b", r"\bopac\b", r"\bbook bank\b",
        r"\bborrow\b", r"\blending\b", r"\blibrary fine\b", r"\breading hall\b",
        r"\blibrary timing\b", r"\blibrarian\b"
    ],
    "academic_syllabus": [
        r"\bsyllabus\b", r"\bcurriculum\b", r"\bscheme\b", r"\bsemester\b",
        r"\bsem\b", r"\bsubject\b", r"\bsubjects\b", r"\bcourse code\b",
        r"\bptu syllabus\b", r"\bikgptu syllabus\b", r"\bstudy material\b",
        r"\bnotes\b", r"\bunit\b", r"\bphp\b", r"\bjava\b", r"\bdata structures\b"
    ],
    "courses_admissions": [
        r"\badmission\b", r"\badmissions\b", r"\beligibility\b", r"\bapply\b",
        r"\bregistration\b", r"\bcounselling\b", r"\bhow to apply\b", r"\bcourses offered\b",
        r"\bprograms\b", r"\bdegrees\b", r"\blateral entry\b", r"\bdocuments required\b",
        r"\bseat\b", r"\bseats\b"
    ],
    "examination_support": [
        r"\bexam\b", r"\bexamination\b", r"\bmst\b", r"\bmid sem\b", r"\bend sem\b",
        r"\battendance\b", r"\b75%\b", r"\bgrading\b", r"\bcgpa\b", r"\bsgpa\b",
        r"\bre-appear\b", r"\bre-checking\b", r"\badmit card\b"
    ],
    "college_info": [
        r"\babout\b", r"\bcgc\b", r"\blandran\b", r"\bplacement\b", r"\bplacements\b",
        r"\bhighest package\b", r"\baverage package\b", r"\brecruiters\b", r"\bcompanies\b",
        r"\bcontact\b", r"\bphone\b", r"\bhelpline\b", r"\bemail\b", r"\baddress\b",
        r"\blocated\b", r"\bnaac\b", r"\bhostel\b", r"\bcampus\b", r"\baffiliation\b"
    ],
    "escalation": [
        r"\bmy\s+(?:private\s+|internal\s+)*(marks|attendance|result|roll\s*number|cgpa)\b",
        r"\b(private\s+record|confidential\s+record)\b",
        r"\bexact fee for my category\b", r"\brefund\b", r"\bcomplaint against\b",
        r"\bhack\b", r"\bpassword reset for portal\b"
    ]
}

COURSES_REGEX = {
    "BCA": r"\bbca\b|\bbachelor of computer applications\b",
    "B.Tech CSE": r"\bb\.?tech\s*cse\b|\bb\.?tech\s*computer\b|\bcse\b|\bcomputer science and engineering\b",
    "B.Tech": r"\bb\.?tech\b|\bengineering\b",
    "MCA": r"\bmca\b|\bmaster of computer applications\b",
    "BBA": r"\bbba\b|\bbachelor of business administration\b",
    "MBA": r"\bmba\b|\bmaster of business administration\b",
    "B.Com": r"\bb\.?com\b|\bcommerce\b",
    "B.Pharm": r"\bb\.?pharm\b|\bbachelor of pharmacy\b|\bpharmacy\b",
    "M.Pharm": r"\bm\.?pharm\b",
    "Biotechnology": r"\bbiotech\b|\bbiotechnology\b|\bmicrobiology\b"
}

SEMESTER_REGEX = r"\b(?:sem|semester)\s*([1-8])\b|\b([1-8])(?:st|nd|rd|th)\s*sem(?:ester)?\b"

SUBJECT_PATTERNS = [
    "php", "python", "java", r"c\+\+", "c programming", "data structures", "dbms",
    "database", "cloud computing", "operating systems", "computer networks",
    "software engineering", "discrete mathematics", "machine learning", "ai",
    "cyber security", "pharmacology", "pharmaceutics", "financial accounting",
    "marketing", "principles of management"
]

class CampusMindRAG:
    """Retrieval-Augmented Generation & Context Memory Engine for CampusMind AI"""
    
    @staticmethod
    def classify_intent(query: str) -> str:
        query_lower = query.lower()
        for pattern in INTENT_PATTERNS["escalation"]:
            if re.search(pattern, query_lower):
                return "escalation"
        from backend.official_answers import detect_intent
        intent = detect_intent(query)
        if intent == "study":
            return "general_ai"
        return intent or "unknown"   # never fall back to a generic "highlights" answer

    @staticmethod
    def extract_context_entities(query: str, current_memory: Optional[Dict] = None) -> Dict[str, Optional[str]]:
        """Extract or inherit course, semester, and subject entities"""
        query_lower = query.lower()
        entities = {
            "course": current_memory.get("course") if current_memory else None,
            "semester": current_memory.get("semester") if current_memory else None,
            "subject": current_memory.get("subject") if current_memory else None
        }
        
        # Check for Course
        for course_name, pattern in COURSES_REGEX.items():
            if re.search(pattern, query_lower):
                entities["course"] = course_name
                break
                
        # Check for Semester
        sem_match = re.search(SEMESTER_REGEX, query_lower)
        if sem_match:
            entities["semester"] = sem_match.group(1) or sem_match.group(2)
            
        # Check for Subject
        for subj in SUBJECT_PATTERNS:
            if re.search(r"\b" + subj + r"\b", query_lower):
                entities["subject"] = subj.upper() if len(subj) <= 4 else subj.title()
                break
                
        return entities

    @staticmethod
    def get_or_create_memory(session_id: str, default_mode: str = "Student") -> Dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student_memory WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if row:
            memory = dict(row)
        else:
            cursor.execute("""
            INSERT INTO student_memory (session_id, course, semester, subject, mode, enabled)
            VALUES (?, NULL, NULL, NULL, ?, 1)
            """, (session_id, default_mode))
            conn.commit()
            memory = {
                "session_id": session_id,
                "course": None,
                "semester": None,
                "subject": None,
                "mode": default_mode,
                "notes": None,
                "enabled": 1
            }
        conn.close()
        return memory

    @staticmethod
    def update_memory(session_id: str, course: Optional[str] = None, semester: Optional[str] = None, 
                      subject: Optional[str] = None, mode: Optional[str] = None) -> Dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        current = CampusMindRAG.get_or_create_memory(session_id)
        
        new_course = course if course is not None else current.get("course")
        new_semester = semester if semester is not None else current.get("semester")
        new_subject = subject if subject is not None else current.get("subject")
        new_mode = mode if mode is not None else current.get("mode")
        
        cursor.execute("""
        UPDATE student_memory 
        SET course = ?, semester = ?, subject = ?, mode = ?, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
        """, (new_course, new_semester, new_subject, new_mode, session_id))
        conn.commit()
        conn.close()
        return CampusMindRAG.get_or_create_memory(session_id)

    @staticmethod
    def clear_memory(session_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE student_memory 
        SET course = NULL, semester = NULL, subject = NULL, notes = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
        """, (session_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def retrieve_documents(query: str, intent: str, context: Optional[Dict] = None, top_k: int = 3) -> List[Dict]:
        """Hybrid keyword & metadata retrieval matching query and student context"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_documents WHERE verified = 1")
        all_docs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        if not all_docs:
            return []
            
        # Clean query tokens
        query_words = set(re.findall(r"\w+", query.lower()))
        stopwords = {"the", "a", "an", "is", "in", "for", "of", "and", "or", "to", "what", "where", "how", "can", "i", "my", "about"}
        content_words = [w for w in query_words if w not in stopwords and len(w) > 2]
        
        course_ctx = (context.get("course") or "").lower() if context else ""
        sem_ctx = (context.get("semester") or "").lower() if context else ""
        subj_ctx = (context.get("subject") or "").lower() if context else ""
        
        scored_docs = []
        for doc in all_docs:
            score = 0.0
            doc_text = f"{doc['title']} {doc['summary']} {doc['content']}".lower()
            tags = json.loads(doc.get("tags") or "[]")
            tags_lower = [t.lower() for t in tags]
            
            # Category boost based on intent
            if doc.get("category") == intent:
                score += 8.0
            if intent == "departments_colleges" and doc.get("id") == "cgc-departments-list":
                score += 15.0
                
            # Token match score
            for word in content_words:
                if word in doc['title'].lower():
                    score += 3.0
                if any(word in t for t in tags_lower):
                    score += 2.5
                if word in doc_text:
                    score += 1.0
                    
            # Context boost
            if course_ctx and (course_ctx in doc_text or any(course_ctx in t for t in tags_lower)):
                score += 4.0
            if sem_ctx and (f"sem {sem_ctx}" in doc_text or f"semester {sem_ctx}" in doc_text):
                score += 3.5
            if subj_ctx and subj_ctx in doc_text:
                score += 4.5
                
            if score > 0:
                scored_docs.append((score, doc))
                
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]
