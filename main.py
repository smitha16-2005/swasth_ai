from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from api.triage import router as triage_router
from api.facilities import router as facility_router
from api.sms import router as sms_router
from core.config import settings
from services.vector_db import load_documents

Base.metadata.create_all(bind=engine)
load_documents()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triage_router)
app.include_router(facility_router)
app.include_router(sms_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version
    }