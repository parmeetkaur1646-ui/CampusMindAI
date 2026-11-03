import os
import json
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from backend.database import get_db_connection, verify_password
from backend.auth import create_jwt_token, require_admin, get_current_user
from backend.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class DocumentCreateRequest(BaseModel):
    category: str
    title: str
    department: Optional[str] = "General"
    academic_year: Optional[str] = "2025-26"
    source_title: str
    source_url: str
    summary: str
    content: str
    tags: Optional[List[str]] = []

def log_audit(admin_user: str, action: str, target: str, details: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO audit_logs (admin_user, action, target, details)
    VALUES (?, ?, ?, ?)
    """, (admin_user, action, target, details))
    conn.commit()
    conn.close()

@router.post("/login")
def admin_login(req: AdminLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role, full_name FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
        
    token = create_jwt_token({
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
        "name": user["full_name"]
    })
    
    log_audit(user["username"], "LOGIN", "Admin Portal", "Successful login")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "role": user["role"],
            "name": user["full_name"]
        }
    }

@router.get("/documents")
def list_documents(user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    docs = []
    for r in rows:
        d = dict(r)
        if d.get("tags"):
            try:
                d["tags"] = json.loads(d["tags"])
            except:
                d["tags"] = []
        docs.append(d)
        
    return {"count": len(docs), "documents": docs}

@router.post("/documents")
def create_document(doc: DocumentCreateRequest, user: dict = Depends(require_admin)):
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO knowledge_documents 
    (id, category, title, department, academic_year, source_title, source_url, verified, tags, summary, content)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
    """, (
        doc_id,
        doc.category,
        doc.title,
        doc.department,
        doc.academic_year,
        doc.source_title,
        doc.source_url,
        json.dumps(doc.tags or []),
        doc.summary,
        doc.content
    ))
    conn.commit()
    conn.close()
    
    log_audit(user.get("sub", "admin"), "CREATE_DOCUMENT", doc.title, f"ID: {doc_id}")
    return {"status": "created", "id": doc_id, "title": doc.title}

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM knowledge_documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    
    log_audit(user.get("sub", "admin"), "DELETE_DOCUMENT", doc_id)
    return {"status": "deleted", "id": doc_id}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("academic_syllabus"),
    department: str = Form("Computer Applications"),
    academic_year: str = Form("2025-26"),
    user: dict = Depends(require_admin)
):
    """Parses uploaded TXT / PDF document and indexes into knowledge base"""
    content = ""
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".txt", ".pdf", ".docx", ".md"]:
        raise HTTPException(status_code=400, detail="Only .txt, .pdf, .docx, and .md files are supported")
        
    raw_bytes = await file.read()
    if ext in [".txt", ".md"]:
        content = raw_bytes.decode("utf-8", errors="ignore")
    else:
        # Fallback text extractor for demo / PDF documents
        content = f"Uploaded verified institutional document: {filename}\n" + raw_bytes.decode("utf-8", errors="ignore")[:3000]
        
    doc_id = f"up-{uuid.uuid4().hex[:8]}"
    title = f"{filename} (Uploaded)"
    summary = f"Institutional document {filename} uploaded for {department} ({academic_year})."
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO knowledge_documents 
    (id, category, title, department, academic_year, source_title, source_url, verified, tags, summary, content)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
    """, (
        doc_id,
        category,
        title,
        department,
        academic_year,
        f"Internal Upload: {filename}",
        "https://www.cgc.edu.in",
        json.dumps(["uploaded", ext.strip("."), department.lower()]),
        summary,
        content
    ))
    conn.commit()
    conn.close()
    
    log_audit(user.get("sub", "admin"), "UPLOAD_DOCUMENT", filename, f"Doc ID: {doc_id}")
    return {"status": "success", "id": doc_id, "filename": filename, "characters_indexed": len(content)}

@router.get("/feedback")
def get_feedback(user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return {"feedback": [dict(r) for r in rows]}

@router.get("/unresolved")
def get_unresolved(user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM unresolved_queries ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return {"unresolved_queries": [dict(r) for r in rows]}

@router.post("/unresolved/{item_id}/resolve")
def resolve_query(item_id: int, user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE unresolved_queries SET status = 'resolved' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    log_audit(user.get("sub", "admin"), "RESOLVE_QUERY", str(item_id))
    return {"status": "resolved", "id": item_id}

@router.get("/audit-logs")
def get_audit_logs(user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    return {"audit_logs": [dict(r) for r in rows]}
