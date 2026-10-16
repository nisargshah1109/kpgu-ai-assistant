from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, conversations, knowledge, health
from app.db import create_tables

app = FastAPI(
    title="KPGU AI University Assistant",
    description="Backend API for KPGU AI University Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])

@app.get("/api/sources", tags=["knowledge"])
async def get_sources_alias():
    return await knowledge.get_sources()

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"message": "KPGU AI University Assistant API"}