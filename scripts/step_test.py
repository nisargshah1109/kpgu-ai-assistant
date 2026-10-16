import sys
import os

print("[STEP 1] Starting script...", flush=True)

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

print("[STEP 2] Environment set up...", flush=True)

from app.db import create_tables, SessionLocal
print("[STEP 3] DB modules imported...", flush=True)

create_tables()
print("[STEP 4] DB tables created...", flush=True)

from app.Models import Conversation
print("[STEP 5] Models imported...", flush=True)

from app.routers.conversations import (
    create_conversation,
    list_conversations,
    get_conversation,
    update_conversation,
    delete_conversation,
    ConversationCreate,
    ConversationUpdate
)
print("[STEP 6] Conversation router imported...", flush=True)

import asyncio

async def test_conv():
    db = SessionLocal()
    conv = await create_conversation(ConversationCreate(title="Step Test"), db=db)
    print(f"[STEP 7] Created conv {conv.id}", flush=True)

    updated = await update_conversation(conv.id, ConversationUpdate(title="New Step Title"), db=db)
    print(f"[STEP 8] Updated title {updated.title}", flush=True)

    await delete_conversation(conv.id, db=db)
    print(f"[STEP 9] Deleted conv {conv.id}", flush=True)
    db.close()

asyncio.run(test_conv())

print("[STEP 10] Importing knowledge router...", flush=True)
from app.routers.knowledge import get_sources, get_knowledge_status
print("[STEP 11] Knowledge router imported...", flush=True)

async def test_know():
    sources = await get_sources()
    print(f"[STEP 12] Sources count: {len(sources)}", flush=True)
    status = await get_knowledge_status()
    print(f"[STEP 13] Status: {status.status}", flush=True)

asyncio.run(test_know())

print("[STEP 14] Finished successfully!", flush=True)
