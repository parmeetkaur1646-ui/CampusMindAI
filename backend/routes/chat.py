import uuid
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.chat_engine import make_reply
from backend.database import get_db_connection
from backend.rag_engine import CampusMindRAG
from backend.ai_service import generate_ai_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    mode: Optional[str] = "Student"

class UpdateMemoryRequest(BaseModel):
    session_id: str
    course: Optional[str] = None
    semester: Optional[str] = None
    subject: Optional[str] = None
    mode: Optional[str] = None

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: Optional[int] = None
    rating: str # 'helpful' or 'not_helpful'
    comment: Optional[str] = None

class UnresolvedRequest(BaseModel):
    session_id: str
    query: str
    contact_email: Optional[str] = None

@router.post("")
def handle_chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    user_query = req.message.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    # 1. Fetch or initialize student context memory
    memory = CampusMindRAG.get_or_create_memory(session_id, default_mode=req.mode)
    
    # 2. Extract entities and update memory if present
    extracted_entities = CampusMindRAG.extract_context_entities(user_query, memory)
    updated_memory = CampusMindRAG.update_memory(
        session_id=session_id,
        course=extracted_entities.get("course"),
        semester=extracted_entities.get("semester"),
        subject=extracted_entities.get("subject"),
        mode=req.mode
    )
    
    # 3. Classify query intent
    intent = CampusMindRAG.classify_intent(user_query)
    
    # 3b. Library / PTU / CGC / Academic questions are understood by the simple keyword engine (backend/chat_engine.py)
    from backend.chat_engine import handle_message
    engine_result = handle_message(user_query, session_id, memory) if intent != "escalation" else None
    if engine_result:
        intent = engine_result["intent"]
        updated_memory = CampusMindRAG.get_or_create_memory(session_id)

    # 4. Retrieve grounded documents from knowledge base (only needed when the engine did not answer)
    retrieved_docs = [] if engine_result else CampusMindRAG.retrieve_documents(user_query, intent, updated_memory, top_k=3)
    
    # 5. Fetch recent conversation history
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT 6",
        (session_id,)
    )
    history_rows = cursor.fetchall()
    history = [dict(r) for r in reversed(history_rows)]
    
    # 6. Generate AI response
    ai_result = engine_result or generate_ai_response(user_query, intent, updated_memory, retrieved_docs, history)
    
    # 7. Persist messages in database
    cursor.execute("""
    INSERT INTO conversations (session_id, role, content, intent, sources_json)
    VALUES (?, 'user', ?, ?, NULL)
    """, (session_id, user_query, intent))
    
    cursor.execute("""
    INSERT INTO conversations (session_id, role, content, intent, sources_json)
    VALUES (?, 'assistant', ?, ?, ?)
    """, (session_id, ai_result["answer"], intent, json.dumps(ai_result.get("sources", []))))
    
    conn.commit()
    conn.close()
    
    return {
        "session_id": session_id,
        "message": ai_result["answer"],
        "intent": intent,
        "sources": ai_result.get("sources", []),
        "follow_up_suggestions": ai_result.get("follow_up_suggestions", []),
        "memory": {
            "course": updated_memory.get("course"),
            "semester": updated_memory.get("semester"),
            "subject": updated_memory.get("subject"),
            "mode": updated_memory.get("mode")
        },
        "grounded": ai_result.get("grounded", True),
        "actions": ai_result.get("actions", []),
        "verification": ai_result.get("verification", "verified" if ai_result.get("grounded", True) else "none")
    }

@router.get("/memory/{session_id}")
def get_memory(session_id: str):
    memory = CampusMindRAG.get_or_create_memory(session_id)
    return {
        "session_id": session_id,
        "memory": memory
    }

@router.post("/memory/update")
def update_memory_api(req: UpdateMemoryRequest):
    updated = CampusMindRAG.update_memory(
        session_id=req.session_id,
        course=req.course,
        semester=req.semester,
        subject=req.subject,
        mode=req.mode
    )
    return {"status": "success", "memory": updated}

@router.post("/memory/clear")
def clear_memory_api(req: UpdateMemoryRequest):
    CampusMindRAG.clear_memory(req.session_id)
    return {"status": "cleared", "session_id": req.session_id}

@router.get("/history/{session_id}")
def get_chat_history(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, role, content, intent, sources_json, created_at FROM conversations WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for r in rows:
        item = dict(r)
        if item.get("sources_json"):
            item["sources"] = json.loads(item["sources_json"])
        else:
            item["sources"] = []
        messages.append(item)
        
    return {"session_id": session_id, "messages": messages}

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO feedback (session_id, message_id, rating, comment)
    VALUES (?, ?, ?, ?)
    """, (req.session_id, req.message_id, req.rating, req.comment))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Feedback recorded. Thank you for helping improve CampusMind AI."}
@router.post("/unresolved")
def report_unresolved(req: UnresolvedRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO unresolved_queries (session_id, query, student_mode, contact_email)
    VALUES (?, ?, 'Student', ?)
    """, (req.session_id, req.query, req.contact_email))
    conn.commit()
    conn.close()
    return {"status": "escalated", "message": "Your query has been logged for review by the campus support team."}
