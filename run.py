#!/usr/bin/env python3
"""
CampusMind AI - Quick Start Launcher
Run this script to initialize the database and start the server:
    python run.py
"""
import os
import sys
import uvicorn

# Ensure the root directory is on the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import settings
from backend.database import init_db

if __name__ == "__main__":
    print("=" * 60)
    print("🎓 CampusMind AI — Context-Aware College Help Desk")
    print("   Chandigarh Group of Colleges (CGC), Landran, Mohali")
    print("=" * 60)
    
    print(">> Initializing SQLite database and Knowledge Base...")
    init_db()
    print(">> Database ready.")
    
    print(f">> Starting server at http://127.0.0.1:{settings.PORT}...")
    print(f">> API Docs available at http://127.0.0.1:{settings.PORT}/docs")
    print("=" * 60)
    
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
