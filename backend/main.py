import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.database import init_db
from backend.routes import chat, academic, library, courses, college, admin, info

# Initialize DB on boot
init_db()

app = FastAPI(
    title="CampusMind AI - CGC Landran College Help Desk",
    description="Context-Aware AI College Help Desk with RAG Knowledge Engine for CGC Landran & PTU",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(info.router)
app.include_router(academic.router)
app.include_router(library.router)
app.include_router(courses.router)
app.include_router(college.router)
app.include_router(admin.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CampusMind AI",
        "institution": "Chandigarh Group of Colleges, Landran",
        "version": "1.0.0"
    }

# Static files and Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "CampusMind AI API is running. Access /docs for API specifications."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)