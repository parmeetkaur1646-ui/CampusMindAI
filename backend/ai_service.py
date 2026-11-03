import json
import re
from typing import Dict, List, Optional
 
import httpx
 
from backend.config import settings
from backend.official_answers import (
    answer_official,
    fallback_ai_unavailable,
    fallback_unknown,
)
 
GROUNDED_SYSTEM = (
    "You are CampusMind AI, the help-desk assistant for Chandigarh Group of Colleges (CGC), Landran. "
    "Answer ONLY from the provided context documents. If the context does not contain the answer, say you "
    "could not find it and suggest contacting the college helpline. Be concise and use Markdown."
)
 
GENERAL_SYSTEM = (
    "You are CampusMind AI, a helpful study assistant for college students (BCA, MCA, B.Tech, MBA, B.Pharm etc.). "
    "Explain topics clearly and concisely with short examples. Use Markdown."
)
 
 
def llm_complete(system: str, user: str, json_mode: bool = False, max_tokens: int = 1200,
                 history: Optional[List[Dict]] = None) -> Optional[str]:
    """One OpenAI-compatible chat call. Returns None if no key is set or the call fails."""
    if not settings.OPENAI_API_KEY:
        return None
    messages = [{"role": "system", "content": system}]
    for h in history or []:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"][:1500]})
    messages.append({"role": "user", "content": user})
    body = {
        "model": settings.AI_MODEL,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        with httpx.Client(timeout=40.0) as client:
            r = client.post(
                f"{settings.AI_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json=body,
            )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None
 
 
def _sources_from_docs(docs: List[Dict]) -> List[Dict]:
    out = []
    for d in docs:
        out.append({
            "title": d.get("title", "Source"),
            "source_title": d.get("source_title") or "CGC Knowledge Base",
            "url": d.get("source_url") or "",
        })
    return out
 
 
def _grounded_from_docs(query: str, docs: List[Dict], history: List[Dict]) -> Dict:
    """Build an answer from retrieved documents; polish with the LLM when available."""
    context = "\n\n".join(
        f"[{i + 1}] {d.get('title', '')}\n{d.get('content', '')}" for i, d in enumerate(docs)
    )
    text = llm_complete(
        GROUNDED_SYSTEM,
        f"Context documents:\n{context}\n\nQuestion: {query}",
        history=history,
    )
    if not text:
        best = docs[0]
        text = f"### {best.get('title', 'Information')}\n\n{best.get('content', '').strip()}"
        if len(docs) > 1:
            text += "\n\n**Related:** " + ", ".join(d.get("title", "") for d in docs[1:])
    return {
        "answer": text,
        "sources": _sources_from_docs(docs),
        "follow_up_suggestions": ["Contact CGC", "Courses offered", "Library rules"],
        "grounded": True,
        "verification": "verified",
        "actions": [],
    }
 
 
def generate_ai_response(query: str, intent: str, memory: Optional[Dict] = None,
                         retrieved_docs: Optional[List[Dict]] = None,
                         history: Optional[List[Dict]] = None) -> Dict:
    """Return {"answer", "sources", "follow_up_suggestions", "grounded", "verification", "actions"}."""
    memory = memory or {}
    retrieved_docs = retrieved_docs or []
    history = history or []
 
    # 0. Private / sensitive requests are escalated, never answered by the AI
    if intent == "escalation":
        return {
            "answer": ("I can't access private records such as your marks, attendance or fee refunds. "
                       "Please contact the college office or use the **Report unresolved query** option "
                       "so the campus support team can help you."),
            "sources": [], "follow_up_suggestions": ["Contact CGC", "Examination information"],
            "grounded": False, "verification": "none", "actions": [],
        }
 
    # 1. Verified official answers
    try:
        official = answer_official(query, intent, memory, retrieved_docs)
    except Exception:
        official = None
    if official:
        official.setdefault("actions", [])
        return official
 
    # 2. General study / concept questions -> LLM
    if intent == "general_ai":
        ctx = ", ".join(f"{k}: {memory[k]}" for k in ("course", "semester", "subject") if memory.get(k))
        prompt = query + (f"\n\n(Student context - {ctx})" if ctx else "")
        text = llm_complete(GENERAL_SYSTEM, prompt, history=history)
        if text:
            return {
                "answer": text, "sources": [],
                "follow_up_suggestions": ["Give me a quiz", "Important questions", "Explain with an example"],
                "grounded": False, "verification": "none", "actions": [],
            }
        result = fallback_ai_unavailable()
        result.setdefault("actions", [])
        return result
 
    # 3. Retrieved knowledge-base documents
    if retrieved_docs:
        return _grounded_from_docs(query, retrieved_docs, history)
 
    # 4. Nothing matched
    result = fallback_unknown()
    result.setdefault("actions", [])
    return result
 