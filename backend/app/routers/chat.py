from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy.orm import Session
from app.db import get_db
from app.Models import Conversation, Message
from app.services.chat_service import ChatService
from app.services.pdf_service import PDFService

router = APIRouter()
chat_service = ChatService()

class ChatRequest(BaseModel):
    conversation_id: int
    message: str

class SourceItem(BaseModel):
    title: str
    url: str
    last_updated: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    message_id: Optional[int] = None
    data_found: bool = True
    is_ambiguous: bool = False
    clarification_options: List[str] = []
    pdf_export_url: Optional[str] = None
    sources: List[SourceItem] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handle chat message using Dataset-Driven Query Handling, Universal Ambiguity Resolution,
    and Explicit PDF Document Export.
    """
    try:
        conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        result = await chat_service.process_chat_message(
            conversation_id=request.conversation_id,
            user_message=request.message,
            db=db
        )

        return ChatResponse(
            conversation_id=result["conversation_id"],
            answer=result["answer"],
            message_id=result.get("message_id"),
            data_found=result.get("data_found", True),
            is_ambiguous=result.get("is_ambiguous", False),
            clarification_options=result.get("clarification_options", []),
            pdf_export_url=result.get("pdf_export_url"),
            sources=result.get("sources", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversations/{conversation_id}/export-pdf")
async def export_conversation_pdf(conversation_id: int, db: Session = Depends(get_db)):
    """
    Export complete conversation thread as a clean downloadable PDF / HTML document.
    """
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
        msg_list = [{"role": m.role, "content": m.content} for m in messages]

        pdf_bytes = PDFService.generate_chat_export_pdf(
            conversation_title=conversation.title or f"Chat_{conversation_id}",
            messages=msg_list
        )

        filename = f"KPGU_Chat_Export_{conversation_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logging.error(f"Error exporting conversation PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF export")