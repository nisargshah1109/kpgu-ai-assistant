import os
import re
import time
import logging
import io
from typing import List, Dict, Any, Optional
from datetime import datetime

import reportlab
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

# PDF Request Detection Regex Patterns
PDF_REQUEST_PATTERNS = [
    r'\b(give|give me|make|generate|genrate|create|export|download|put|save)\b.*\b(pdf|document|doc|file)\b',
    r'\bpdf for\b',
    r'\bin pdf\b',
    r'\bpdf format\b',
    r'\bdownload chat\b',
    r'\bexport chat\b',
    r'\bexport conversation\b'
]

class PDFService:
    """
    Topic-Agnostic User-Controlled PDF & Document Generator.
    Generates native, high-quality PDF documents using ReportLab.
    Ensures zero leakage of system prompts, secret keys, or internal metadata.
    """

    @staticmethod
    def is_pdf_requested(query: str) -> bool:
        """Detects if user explicitly asked for a PDF / document export in text"""
        if not query:
            return False
        q_lower = query.lower()
        return any(re.search(pattern, q_lower) for pattern in PDF_REQUEST_PATTERNS)

    @staticmethod
    def generate_chat_export_pdf(conversation_title: str, messages: List[Dict[str, str]]) -> bytes:
        """
        Generates a clean, native PDF document of the entire conversation thread.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a')
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#2563eb')
        )

        meta_style = ParagraphStyle(
            'DocMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748b')
        )

        user_role_style = ParagraphStyle(
            'UserRole',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#1e40af')
        )

        assistant_role_style = ParagraphStyle(
            'AssistantRole',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#047857')
        )

        msg_body_style = ParagraphStyle(
            'MsgBody',
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#1e293b')
        )

        footer_style = ParagraphStyle(
            'Footer',
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            alignment=1, # Center
            textColor=colors.HexColor('#64748b')
        )

        story = []

        # Header Section
        story.append(Paragraph("Drs. Kiran & Pallavi Patel Global University (KPGU)", title_style))
        story.append(Paragraph(f"Chat Export: {conversation_title or 'Conversation Thread'}", subtitle_style))
        date_str = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
        story.append(Paragraph(f"Export Date: {date_str}", meta_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=5, spaceAfter=15))

        # Messages Flow
        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "").replace("\n", "<br/>")

            if role == "user":
                header_p = Paragraph("User Query", user_role_style)
                bg_color = colors.HexColor('#eff6ff')
                border_color = colors.HexColor('#bfdbfe')
            else:
                header_p = Paragraph("KPGU AI Assistant", assistant_role_style)
                bg_color = colors.HexColor('#f0fdf4')
                border_color = colors.HexColor('#bbf7d0')

            body_p = Paragraph(content, msg_body_style)
            msg_table = Table([[header_p], [body_p]], colWidths=[540])
            msg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ('BOX', (0, 0), (-1, -1), 0.75, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))

            story.append(msg_table)
            story.append(Spacer(1, 10))

        # Footer Section
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=10, spaceAfter=10))
        story.append(Paragraph("Official KPGU Knowledge Base Document &bull; Made with ❤️ by Nisarg Shah &amp; Harsh Shah &bull; KPGU Students", footer_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_topic_pdf(topic_title: str, topic_content: str, sources: List[Dict[str, str]] = None) -> bytes:
        """
        Generates a clean, topic-specific PDF document for any dataset topic (KSET, Admissions, Fees, Hostel, etc.).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TopicTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a')
        )
        
        subtitle_style = ParagraphStyle(
            'TopicSubTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#2563eb')
        )

        meta_style = ParagraphStyle(
            'TopicMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748b')
        )

        content_style = ParagraphStyle(
            'TopicContent',
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=colors.HexColor('#1e293b')
        )

        source_title_style = ParagraphStyle(
            'SourceTitle',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#1e3a8a')
        )

        source_item_style = ParagraphStyle(
            'SourceItem',
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#2563eb')
        )

        footer_style = ParagraphStyle(
            'Footer',
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            alignment=1,
            textColor=colors.HexColor('#64748b')
        )

        story = []

        # Header
        story.append(Paragraph("Drs. Kiran & Pallavi Patel Global University (KPGU)", title_style))
        story.append(Paragraph(f"Official Information Document: {topic_title}", subtitle_style))
        date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"Issued Date: {date_str}", meta_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=5, spaceAfter=15))

        # Main Content Box
        clean_content = topic_content.replace("\n", "<br/>")
        body_p = Paragraph(clean_content, content_style)
        content_table = Table([[body_p]], colWidths=[540])
        content_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(content_table)
        story.append(Spacer(1, 15))

        # Verified Sources
        if sources:
            story.append(Paragraph("Verified Sources & Data References:", source_title_style))
            story.append(Spacer(1, 5))
            for src in sources:
                src_str = f"&bull; <b>{src.get('title', 'KPGU Portal')}</b>: {src.get('url', '')}"
                story.append(Paragraph(src_str, source_item_style))
            story.append(Spacer(1, 15))

        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=10, spaceAfter=10))
        story.append(Paragraph("Official KPGU Knowledge Base Document &bull; Made with ❤️ by Nisarg Shah &amp; Harsh Shah &bull; KPGU Students", footer_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
