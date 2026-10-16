import sys
import os
import asyncio

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

res_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_results.txt'))

def log(msg):
    with open(res_file, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

with open(res_file, "w", encoding="utf-8") as f:
    f.write("=== KPGU Assistant Direct Function Verification ===\n")

log("Starting direct verification...")

from app.db import create_tables, SessionLocal
create_tables()
log("1. DB tables created successfully.")

db = SessionLocal()

from app.routers.conversations import (
    create_conversation,
    list_conversations,
    get_conversation,
    update_conversation,
    delete_conversation,
    ConversationCreate,
    ConversationUpdate
)

async def test_conversations():
    # Create
    conv = await create_conversation(ConversationCreate(title="Direct Test"), db=db)
    log(f"2. Created conversation ID: {conv.id}, Title: {conv.title}")
    assert conv.id is not None

    # Get
    c = await get_conversation(conv.id, db=db)
    log(f"3. Retrieved conversation ID: {c.id}")

    # Update (PUT title)
    updated = await update_conversation(conv.id, ConversationUpdate(title="Updated Direct Title"), db=db)
    log(f"4. Updated title: {updated.title}")
    assert updated.title == "Updated Direct Title"

    # List
    convs = await list_conversations(db=db)
    log(f"5. Listed {len(convs)} conversations.")

    # Delete
    del_res = await delete_conversation(conv.id, db=db)
    log(f"6. Delete conversation result: {del_res}")

asyncio.run(test_conversations())

from app.routers.knowledge import get_sources, get_knowledge_status

async def test_knowledge():
    sources = await get_sources()
    log(f"7. Sources returned: {len(sources)} sources.")
    status = await get_knowledge_status()
    log(f"8. Knowledge status: {status.status}, Docs: {status.document_count}, Chunks: {status.chunk_count}")

asyncio.run(test_knowledge())

from app.services.text_processor import TextProcessor
tp = TextProcessor()
cleaned = tp.clean_text("   KPGU   Assistant   ")
log(f"9. Text cleaning test: '{cleaned}'")
assert cleaned == "KPGU Assistant"

log("=== ALL DIRECT TESTS COMPLETED SUCCESSFULLY ===")
db.close()
