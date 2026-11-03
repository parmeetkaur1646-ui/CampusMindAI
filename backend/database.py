import sqlite3
import json
import os
import hashlib
from datetime import datetime
from backend.config import settings

def get_db_connection():
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    # PBKDF2 HMAC SHA-256 for secure password storage without heavy compiled binary dependencies
    salt = "cgc_landran_campusmind_salt_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_password(plain_password: str, hashed: str) -> bool:
    return hash_password(plain_password) == hashed

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Student Context Memory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_memory (
        session_id TEXT PRIMARY KEY,
        course TEXT,
        semester TEXT,
        subject TEXT,
        mode TEXT DEFAULT 'Student',
        notes TEXT,
        enabled INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Conversations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        intent TEXT,
        sources_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 4. Knowledge Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        department TEXT,
        academic_year TEXT,
        source_title TEXT,
        source_url TEXT,
        verified INTEGER DEFAULT 1,
        tags TEXT,
        summary TEXT,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 5. Feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        message_id INTEGER,
        rating TEXT NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 6. Unresolved Queries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unresolved_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        query TEXT NOT NULL,
        student_mode TEXT,
        status TEXT DEFAULT 'pending',
        contact_email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 7. Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_user TEXT NOT NULL,
        action TEXT NOT NULL,
        target TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Seed default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ('admin', hash_password('admin123'), 'admin', 'CGC Administrator')
        )
    
    # Seed or sync Knowledge Base from JSON file
    if os.path.exists(settings.KB_FILE_PATH):
        try:
            with open(settings.KB_FILE_PATH, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
                for doc in kb_data.get('documents', []):
                    cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_documents 
                    (id, category, title, department, academic_year, source_title, source_url, verified, tags, summary, content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc.get('id'),
                        doc.get('category'),
                        doc.get('title'),
                        doc.get('department'),
                        doc.get('academic_year'),
                        doc.get('source_title'),
                        doc.get('source_url'),
                        1 if doc.get('verified', True) else 0,
                        json.dumps(doc.get('tags', [])),
                        doc.get('summary'),
                        doc.get('content')
                    ))
        except Exception as e:
            print(f"Error seeding KB: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
