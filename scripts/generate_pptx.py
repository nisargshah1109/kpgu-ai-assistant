import sys
import os

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    os.system(f"{sys.executable} -m pip install python-pptx")
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors (Dark Slate & Electric Blue)
    BG_COLOR = RGBColor(15, 23, 42)       # #0f172a
    CARD_BG = RGBColor(30, 41, 59)        # #1e293b
    ACCENT_BLUE = RGBColor(56, 189, 248)  # #38bdf8
    WHITE = RGBColor(255, 255, 255)
    GRAY = RGBColor(148, 163, 184)        # #94a3b8

    def add_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return slide

    def add_header(slide, title_text, category="KPGU AI ASSISTANT"):
        # Header category
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        # Main Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.8))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = WHITE

    # --- SLIDE 1: Title Slide ---
    slide1 = add_bg(prs.slides.add_slide(blank_layout))
    
    # Title Box
    tbox = slide1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.333), Inches(3.0))
    tf1 = tbox.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "KPGU AI Assistant"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = ACCENT_BLUE

    p2 = tf1.add_paragraph()
    p2.text = "Next-Generation RAG-Powered AI University Assistant"
    p2.font.size = Pt(22)
    p2.font.color.rgb = WHITE

    p3 = tf1.add_paragraph()
    p3.text = "\nDrs. Kiran & Pallavi Patel Global University (KPGU), Vadodara"
    p3.font.size = Pt(14)
    p3.font.color.rgb = GRAY

    p4 = tf1.add_paragraph()
    p4.text = "Tech Stack: React 19 • Vite • Tailwind CSS v4 • FastAPI • Python 3.13 • FAISS • Google Gemini AI"
    p4.font.size = Pt(12)
    p4.font.color.rgb = ACCENT_BLUE

    # --- SLIDE 2: Problem Statement & Opportunity ---
    slide2 = add_bg(prs.slides.add_slide(blank_layout))
    add_header(slide2, "Problem Statement & Opportunity", "CHALLENGE & VISION")

    # Left Card (Problem)
    c1 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    c1.fill.solid(); c1.fill.fore_color.rgb = CARD_BG; c1.line.color.rgb = ACCENT_BLUE
    tf_c1 = c1.text_frame; tf_c1.word_wrap = True
    p = tf_c1.paragraphs[0]; p.text = "🚨 Traditional Challenges"; p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = ACCENT_BLUE
    
    bullets1 = [
        "Fragmented Information: University sites contain 100+ pages making quick lookups hard.",
        "Static FAQ Limitations: Search bars return rigid, outdated keywords instead of direct answers.",
        "Repetitive Inquiries: High staff workload handling routine queries for Admissions, D2D, Fees, and Hostel.",
        "Delayed Response Times: Students wait days for email or phone query resolutions."
    ]
    for b in bullets1:
        p = tf_c1.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(13)
        p.font.color.rgb = WHITE

    # Right Card (Opportunity)
    c2 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    c2.fill.solid(); c2.fill.fore_color.rgb = CARD_BG; c2.line.color.rgb = ACCENT_BLUE
    tf_c2 = c2.text_frame; tf_c2.word_wrap = True
    p = tf_c2.paragraphs[0]; p.text = "💡 The Opportunity"; p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = ACCENT_BLUE

    bullets2 = [
        "Instant 24/7 AI Guidance: Real-time accurate answers powered by Retrieval-Augmented Generation.",
        "Domain Specificity: Tailored specifically for KPGU Vadodara admissions, D2D, and facilities.",
        "Dual-Engine Fallback: Generative AI LLM synthesis paired with direct Knowledge Synthesizer.",
        "Modern Responsive UX: Premium glassmorphism UI built for desktop and mobile devices."
    ]
    for b in bullets2:
        p = tf_c2.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(13)
        p.font.color.rgb = WHITE

    # --- SLIDE 3: System Architecture & Workflow ---
    slide3 = add_bg(prs.slides.add_slide(blank_layout))
    add_header(slide3, "System Architecture & Data Flow", "TECHNICAL DESIGN")

    cards_data = [
        ("1. Frontend UI", "React 19 + Vite 8\nTailwind CSS v4\nGlassmorphism Theme\nAxios Async Client", Inches(0.8)),
        ("2. Backend API", "FastAPI (Python 3.13)\nAsync Event Loop\nCORS Middleware\nSQLAlchemy ORM", Inches(3.8)),
        ("3. Vector RAG", "SentenceTransformers\nFAISS Vector Store\n111+ Indexed Chunks\nNumPy Similarity", Inches(6.8)),
        ("4. AI Synthesis", "Google Gemini 1.5\nGenerative Prompting\nThread Pool Execution\nFallback Engine", Inches(9.8))
    ]

    for title, desc, left in cards_data:
        c = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(2.2), Inches(2.7), Inches(4.2))
        c.fill.solid(); c.fill.fore_color.rgb = CARD_BG; c.line.color.rgb = ACCENT_BLUE
        tf = c.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = title; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = ACCENT_BLUE
        p2 = tf.add_paragraph(); p2.text = f"\n{desc}"; p2.font.size = Pt(13); p2.font.color.rgb = WHITE

    # --- SLIDE 4: Core Domain Modules ---
    slide4 = add_bg(prs.slides.add_slide(blank_layout))
    add_header(slide4, "Intelligent Domain Knowledge Modules", "FEATURES & CAPABILITIES")

    modules = [
        ("🎓 Admissions", "Step-by-step application guidance, eligibility rules, and document verification criteria."),
        ("🔄 Diploma to Degree (D2D)", "Direct 2nd-year B.Tech / B.Pharm admission rules, ACPC counseling, and diploma requirements."),
        ("💻 Computer Science & Fees", "B.Tech Computer Engineering tuition fees (~₹85k-95k/yr), GUJCET/JEE exam scores, and AI tracks."),
        ("🏫 Hostel & Amenities", "Boys/Girls AC & Non-AC room rates (₹65k-85k/yr), 24/7 security, Wi-Fi, and mess dining."),
        ("💼 Placements", "150+ corporate recruiters (TCS, Wipro, L&T, Sun Pharma) and highest packages up to ₹12 LPA.")
    ]

    top_pos = Inches(1.8)
    for title, desc in modules:
        c = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_pos, Inches(11.7), Inches(0.9))
        c.fill.solid(); c.fill.fore_color.rgb = CARD_BG; c.line.color.rgb = ACCENT_BLUE
        tf = c.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = f"{title}: "; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = ACCENT_BLUE
        # Add description inline
        run = p.add_run()
        run.text = desc
        run.font.size = Pt(13)
        run.font.bold = False
        run.font.color.rgb = WHITE
        top_pos += Inches(1.05)

    # --- SLIDE 5: Conclusion & Future Scope ---
    slide5 = add_bg(prs.slides.add_slide(blank_layout))
    add_header(slide5, "Conclusion & Future Roadmap", "SUMMARY & NEXT STEPS")

    c_left = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    c_left.fill.solid(); c_left.fill.fore_color.rgb = CARD_BG; c_left.line.color.rgb = ACCENT_BLUE
    tf_l = c_left.text_frame; tf_l.word_wrap = True
    p = tf_l.paragraphs[0]; p.text = "🎯 Project Summary"; p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = ACCENT_BLUE
    
    summary_items = [
        "Production-Grade RAG Assistant built for KPGU Vadodara.",
        "Zero-latency response with FAISS vector search & Gemini AI.",
        "100% High Availability fallback mechanism.",
        "Premium glassmorphism dark theme UI."
    ]
    for item in summary_items:
        p = tf_l.add_paragraph()
        p.text = f"✔ {item}"
        p.font.size = Pt(13)
        p.font.color.rgb = WHITE

    c_right = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    c_right.fill.solid(); c_right.fill.fore_color.rgb = CARD_BG; c_right.line.color.rgb = ACCENT_BLUE
    tf_r = c_right.text_frame; tf_r.word_wrap = True
    p = tf_r.paragraphs[0]; p.text = "🚀 Future Scope"; p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = ACCENT_BLUE

    future_items = [
        "Multilingual Support: Voice & text queries in Gujarati and Hindi.",
        "WhatsApp & Telegram Integration: Direct messaging bot outreach.",
        "Voice Assistant: Speech-to-text input and audio responses.",
        "Analytics Portal: Insights on top student questions & trends."
    ]
    for item in future_items:
        p = tf_r.add_paragraph()
        p.text = f"🚀 {item}"
        p.font.size = Pt(13)
        p.font.color.rgb = WHITE

    # Save Presentation
    output_path = "KPGU_AI_Assistant_Presentation.pptx"
    prs.save(output_path)
    print(f"SUCCESSFULLY_CREATED: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_presentation()
