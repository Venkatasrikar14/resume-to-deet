import streamlit as st
import json
import os
import base64
from extraction.parser import parse_resume, extract_text_from_pdf, extract_text_from_image
from intelligence import run_intelligence

# ─────────────────────────────────────────────────────────────────────────────
# LOAD LOCAL LOGO — base64-encode so it can be used inside st.markdown HTML
# ─────────────────────────────────────────────────────────────────────────────
_logo_b64 = ""
_logo_path = os.path.join(os.path.dirname(__file__), "telangana_emblem.png")
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode("utf-8")
_logo_src = f"data:image/png;base64,{_logo_b64}" if _logo_b64 else ""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DEET AI | Career Bridge - Telangana",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Government Portal Theme
# Edit hex codes in the comments to tweak the colour palette.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* === GOOGLE FONT === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── BUG FIX 1: Force text visible on light background ────────────────────
   Target ONLY text-bearing HTML elements. Never use * wildcard with color —
   it leaks into SVG <title>/<desc> tags and shows hidden labels like
   "arrowdown" as visible text on the page.                                  */
.stApp {
    font-family: 'Inter', sans-serif;
    color: #1F2937;
}
.stApp p, .stApp span, .stApp div, .stApp label,
.stApp li, .stApp td, .stApp th, .stApp a,
.stApp input, .stApp textarea, .stApp select, .stApp option,
.stApp summary, .stApp figcaption, .stApp blockquote,
.stApp dt, .stApp dd, .stApp small, .stApp strong, .stApp em {
    font-family: 'Inter', sans-serif;
    color: #1F2937;  /* near-black, readable on white/light gray */
}
/* Make sure SVG internals are NEVER styled with text color */
.stApp svg, .stApp svg * {
    color: unset !important;
}
.stApp svg title, .stApp svg desc {
    display: none !important;
}

/* ── Main page headings: Government Blue ────────────────────────────────── */
.stApp h1, .stApp h2 {
    color: #003366 !important;  /* #003366 — deep institutional blue */
    font-weight: 700 !important;
}
.stApp h3, .stApp h4 {
    color: #1e3a5f !important;  /* #1e3a5f — slightly lighter blue */
    font-weight: 600 !important;
}

/* ── BUG FIX 2: REMOVE phantom white boxes ───────────────────────────────
   NEVER apply background/shadow to Streamlit's internal layout divs.
   Only our explicit .card class gets card styling.                         */
.stApp {
    background-color: #f0f4f8;  /* #f0f4f8 — muted blue-gray page bg */
}

/* Reset any accidental backgrounds on Streamlit layout wrappers */
section[data-testid="stMain"],
div[data-testid="stVerticalBlock"],
/* div[data-testid="stVerticalBlockBorderWrapper"], */
div[data-testid="stHorizontalBlock"],
div[data-testid="column"],
div[data-testid="stAppViewBlockContainer"] {
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
}

/* === HIDE DEFAULT STREAMLIT CHROME === */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    max-width: 1300px !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   GOVERNMENT HEADER BAR
   Primary brand: deep institutional blue
═══════════════════════════════════════════════════════════════════════════ */
.gov-header {
    background: linear-gradient(135deg, #002244 0%, #003a6e 100%);  /* #002244 → #003a6e */
    padding: 0;
    margin: 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    position: sticky;
    top: 0;
    z-index: 999;
}
.gov-header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
    padding: 12px 32px;
    max-width: 1300px;
    margin: 0 auto;
}
.gov-logo-block { display: flex; align-items: center; gap: 14px; }
.gov-emblem { font-size: 2rem; line-height: 1; }
.gov-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff !important;  /* header text must remain white */
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 0;
}
.gov-subtitle {
    font-size: 0.7rem;
    color: #a8c8e8 !important;  /* #a8c8e8 — pale blue subtitle */
    letter-spacing: 0.08em;
    margin: 4px 0 0 0;
    line-height: 1.3;
}
.gov-nav { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }
.gov-nav a {
    color: #cbd9ea !important;  /* #cbd9ea — nav link */
    text-decoration: none;
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    transition: color 0.2s;
}
.gov-nav a:hover { color: #ffffff !important; }
.gov-nav .active { color: #ffd700 !important; font-weight: 600; }  /* #ffd700 — gold active */

/* ══════════════════════════════════════════════════════════════════════════
   PAGE TITLE BAND
═══════════════════════════════════════════════════════════════════════════ */
.page-band {
    background: #ffffff;
    border-bottom: 3px solid #003366;  /* #003366 — blue accent underline */
    padding: 14px 32px;
    margin-bottom: 24px;
}
.page-band h2 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #003366 !important;
    letter-spacing: 0.04em;
}
.page-band .breadcrumb {
    font-size: 0.72rem;
    color: #888 !important;
    margin-top: 2px;
}

/* ══════════════════════════════════════════════════════════════════════════
   STREAMLIT NATIVE CARDS
   Style Streamlit's Bordered Containers to be our white cards
═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    margin-bottom: 20px !important;
    padding: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 24px 28px !important;
}
.card-title {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #003366 !important;  /* #003366 — deep blue section title */
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 10px;
    margin-bottom: 18px;
}

/* ══════════════════════════════════════════════════════════════════════════
   SKILL PILL TAGS — light blue
═══════════════════════════════════════════════════════════════════════════ */
.skill-pill {
    display: inline-block;
    background-color: #dbeafe;  /* #dbeafe — light blue */
    color: #1e40af !important;  /* #1e40af — deep blue text */
    border: 1px solid #bfdbfe;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 4px 4px 4px 0;
}

/* ══════════════════════════════════════════════════════════════════════════
   AMBER ALERT BOX — Skill Gaps
═══════════════════════════════════════════════════════════════════════════ */
.alert-amber {
    background-color: #fffbeb;  /* #fffbeb — pale amber */
    border-left: 4px solid #f59e0b;  /* #f59e0b — amber accent */
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.alert-amber .alert-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #92400e !important;  /* #92400e — dark amber */
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
}
.alert-amber .gap-tag {
    display: inline-block;
    background: #fde68a;  /* #fde68a — amber pill */
    color: #78350f !important;  /* #78350f — amber text */
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 3px 4px 3px 0;
}

/* ══════════════════════════════════════════════════════════════════════════
   RECOMMENDATION CARDS — gray with sky-blue left accent
═══════════════════════════════════════════════════════════════════════════ */
.rec-card {
    background: #f8fafc;  /* #f8fafc — very light gray */
    border: 1px solid #e2e8f0;
    border-left: 4px solid #0ea5e9;  /* #0ea5e9 — sky blue accent */
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 0.85rem;
    color: #1e293b !important;  /* #1e293b — near-black */
    line-height: 1.55;
}
.rec-card .rec-num {
    display: inline-block;
    background: #0ea5e9;
    color: white !important;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    text-align: center;
    line-height: 22px;
    font-size: 0.7rem;
    font-weight: 700;
    margin-right: 8px;
}

/* ══════════════════════════════════════════════════════════════════════════
   INFERRED ROLE BADGE — dark blue gradient
═══════════════════════════════════════════════════════════════════════════ */
.role-badge {
    background: linear-gradient(135deg, #003366 0%, #0052a3 100%);
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 14px;
}
.role-badge .role-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #a8c8e8 !important;
    margin-bottom: 4px;
}
.role-badge .role-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff !important;
}
.role-badge .domain-value {
    font-size: 0.82rem;
    color: #cbd9ea !important;
    margin-top: 4px;
}

/* ══════════════════════════════════════════════════════════════════════════
   CONFIDENCE METER
═══════════════════════════════════════════════════════════════════════════ */
.conf-row { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.conf-score-box {
    background: #003366;
    border-radius: 10px;
    padding: 10px 18px;
    text-align: center;
    min-width: 70px;
}
.conf-score-box .score { font-size: 1.6rem; font-weight: 700; color: #ffffff !important; }
.conf-score-box .label {
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #a8c8e8 !important;
}
.conf-just { font-size: 0.82rem; color: #475569 !important; line-height: 1.55; flex: 1; }

/* ══════════════════════════════════════════════════════════════════════════
   ACTION BUTTONS — deep government green
═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stButton"] > button {
    background-color: #1B5E20 !important;  /* #1B5E20 — deep green */
    color: #ffffff !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 14px 28px !important;
    width: 100% !important;
    transition: background-color 0.2s, transform 0.1s !important;
    box-shadow: 0 4px 12px rgba(27,94,32,0.3) !important;
}
div[data-testid="stButton"] > button:hover {
    background-color: #2E7D32 !important;  /* #2E7D32 — lighter green hover */
    transform: translateY(-1px) !important;
}
div[data-testid="stDownloadButton"] > button {
    background-color: #003366 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    width: 100% !important;
    border: none !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background-color: #004080 !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   BUG FIX 3: INPUT FIELDS — force white background + dark text
   Defeats dark-mode inheritance on text inputs, textareas, selectboxes.
═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    background-color: #ffffff !important;  /* white bg */
    color: #1F2937 !important;            /* dark text */
    border: 1px solid #cbd5e1 !important; /* #cbd5e1 — gray border */
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #003366 !important;
    box-shadow: 0 0 0 2px rgba(0,51,102,0.15) !important;
    outline: none !important;
}

/* Selectbox container */
div[data-testid="stSelectbox"] > div > div {
    background-color: #ffffff !important;
    color: #1F2937 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}

/* Form labels — small, uppercase, government blue */
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #374151 !important;  /* #374151 — dark gray label */
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   BUG FIX 3 cont: FILE UPLOADER — white bg, dark text, blue dashed border
═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stFileUploader"],
div[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploaderDropzone"] > div {
    background: #f0f6ff !important;       /* very light blue-white */
    background-color: #f0f6ff !important;
}
div[data-testid="stFileUploader"] {
    border: 2px dashed #93c5fd !important;
    border-radius: 10px !important;
    padding: 12px !important;
}
div[data-testid="stFileUploader"] * {
    color: #1e3a5f !important;            /* dark blue text throughout */
    background-color: transparent !important;
}
div[data-testid="stFileUploaderDropzoneInstructions"] {
    background: transparent !important;
}

/* ── BUG FIX 4: Expander 'arrowdown' SVG label leaking as visible text ─────
   Our global .stApp * color rule makes the SVG <title> element's text show. */
div[data-testid="stExpander"] summary svg title,
div[data-testid="stExpander"] summary svg desc {
    display: none !important;
    visibility: hidden !important;
    font-size: 0 !important;
}

/* Expander headers */
div[data-testid="stExpander"] summary {
    background: #f1f5f9 !important;
    border-radius: 8px !important;
    color: #1e3a5f !important;
    font-weight: 600 !important;
    overflow: hidden !important;
}

/* Streamlit info/success/warning boxes — ensure readable text */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
}
div[data-testid="stAlert"] p {
    color: inherit !important;
}

/* Progress bar */
div[data-testid="stProgressBar"] > div {
    border-radius: 999px !important;
}

/* Divider */
hr { border-color: #e2e8f0 !important; margin: 20px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GOVERNMENT HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="gov-header">
  <div class="gov-header-inner">
    <div class="gov-logo-block">
      <div class="gov-emblem">
        <img src="{_logo_src}" alt="Telangana Emblem" style="height: 54px; width: auto;">
      </div>
      <div class="gov-title-block">
        <p class="gov-title">DEET AI | Career Bridge — Telangana</p>
        <p class="gov-subtitle">Digital Employment Exchange Telangana</p>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE TITLE BAND
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-band">
  <h2>🔍 AI-Powered Profile &amp; Skill Gap Analysis</h2>
  <div class="breadcrumb">Home &rsaquo; Citizen Services &rsaquo; Resume AI Analysis</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
with st.container():
    with st.container(border=True):
        st.markdown('<div class="card-title">📄 Upload Citizen Resume</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF, JPG, or PNG) — AI will extract and analyse your profile automatically.",
            type=["pdf", "jpg", "jpeg", "png"],
            label_visibility="visible"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT — only shown after upload
# ─────────────────────────────────────────────────────────────────────────────
if uploaded_file is not None:
    with st.spinner("🔄 Extracting profile and running AI career analysis..."):

        # ── Backend extraction (DO NOT MODIFY) ──────────────────────────────
        original_ext = os.path.splitext(uploaded_file.name)[1].lower() or ".pdf"
        temp_path = f"temp_resume{original_ext}"

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if original_ext in [".jpg", ".jpeg", ".png"]:
            raw_text = extract_text_from_image(temp_path)
            if isinstance(raw_text, str) and raw_text.startswith('{"error"'):
                raw_text = ""
        else:
            raw_text = extract_text_from_pdf(temp_path)

        resume_data = parse_resume(temp_path)

        if isinstance(resume_data, str) and "error" in resume_data:
            st.error("❌ Failed to parse the document. Please try a clearer scan or a different file.")
            st.stop()

        intelligence_data = run_intelligence(resume_data, raw_text)

        # Merge LLM fallbacks
        if not resume_data.get("skills"):
            resume_data["skills"] = intelligence_data.get("skills", [])
        if not resume_data.get("education"):
            llm_edu = intelligence_data.get("education", [])
            if llm_edu and llm_edu != ["N/A"]:
                resume_data["education"] = [
                    {"degree": edu, "specialization": "", "institution": "", "year": "", "cgpa": ""}
                    for edu in llm_edu if edu
                ]
        # ── End backend extraction ───────────────────────────────────────────

    st.success("✅ Profile extracted and AI analysis complete.")

    # ─── TWO-COLUMN LAYOUT ───────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1.2], gap="large")

    # ════════════════════════════════════════════════════════════════════════
    # LEFT COLUMN — Citizen Profile (editable form)
    # ════════════════════════════════════════════════════════════════════════
    with col1:
        # ── Personal & Contact ───────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="card-title">👤 Citizen Profile</div>', unsafe_allow_html=True)

            personal = resume_data.get("personal", {})
            contact  = resume_data.get("contact",  {})

            full_name = st.text_input("Full Name",  value=personal.get("full_name", ""))
            email     = st.text_input("Email",      value=contact.get("email", ""))
            phone     = st.text_input("Mobile",     value=contact.get("phone", ""))
            linkedin  = st.text_input("LinkedIn",   value=contact.get("linkedin", ""))
            github    = st.text_input("GitHub / Portfolio", value=contact.get("github_or_portfolio", ""))
            location  = st.text_input("Location",   value=personal.get("location", ""))

            resume_data["personal"] = {"full_name": full_name, "location": location, "address": ""}
            resume_data["contact"]  = {
                "email": email, "phone": phone,
                "linkedin": linkedin, "github_or_portfolio": github
            }


        # ── Education ────────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="card-title">🎓 Education</div>', unsafe_allow_html=True)

            education_list  = resume_data.get("education", [])
            updated_education = []

            if not education_list:
                st.info("No education details found. Please fill in manually.")
            else:
                for i, edu in enumerate(education_list):
                    with st.expander(f"Degree {i+1}: {edu.get('degree', 'Unknown')}", expanded=(i == 0)):
                        c1, c2 = st.columns(2)
                        with c1:
                            degree = st.text_input("Degree",         value=edu.get("degree", ""),         key=f"deg_{i}")
                            spec   = st.text_input("Specialization", value=edu.get("specialization", ""),  key=f"spc_{i}")
                            inst   = st.text_input("Institution",    value=edu.get("institution", ""),     key=f"ins_{i}")
                        with c2:
                            year   = st.text_input("Year",           value=edu.get("year", ""),            key=f"yr_{i}")
                            cgpa   = st.text_input("CGPA / Grade",   value=edu.get("cgpa", ""),            key=f"cgpa_{i}")
                        updated_education.append({"degree": degree, "specialization": spec,
                                                   "institution": inst, "year": year, "cgpa": cgpa})

            resume_data["education"] = updated_education

            # ── Extracted Skills — pill tags ─────────────────────────────────────

        with st.container(border=True):
            st.markdown('<div class="card-title">🛠 Extracted Skills</div>', unsafe_allow_html=True)

            skills = resume_data.get("skills", [])
            if skills:
                pills_html = "".join(
                    f'<span class="skill-pill">{s}</span>' for s in skills if s
                )
                st.markdown(f'<div style="margin-bottom:12px; line-height: 2.5;">{pills_html}</div>', unsafe_allow_html=True)
            else:
                st.caption("No skills detected automatically.")

            skills_str         = ", ".join(skills)
            updated_skills_str = st.text_area("Edit Skills (comma-separated)", value=skills_str, height=80)
            resume_data["skills"] = [s.strip() for s in updated_skills_str.split(",") if s.strip()]


        # ── Experience ───────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="card-title">💼 Work Experience</div>', unsafe_allow_html=True)

            experience_list   = resume_data.get("experience", [])
            updated_experience = []

            if not experience_list:
                st.info("No experience details found.")
            else:
                for i, exp in enumerate(experience_list):
                    label = f"{exp.get('role','Role')} @ {exp.get('company','Company')}"
                    with st.expander(label, expanded=(i == 0)):
                        cx1, cx2 = st.columns(2)
                        with cx1:
                            company  = st.text_input("Company",  value=exp.get("company",  ""), key=f"cmp_{i}")
                            role     = st.text_input("Role",     value=exp.get("role",     ""), key=f"rol_{i}")
                        with cx2:
                            duration = st.text_input("Duration", value=exp.get("duration", ""), key=f"dur_{i}")
                        description = st.text_area("Description", value=exp.get("description", ""),
                                                   height=80, key=f"dsc_{i}")
                        updated_experience.append({"company": company, "role": role,
                                                    "duration": duration, "description": description})

            resume_data["experience"] = updated_experience


    # ════════════════════════════════════════════════════════════════════════
    # RIGHT COLUMN — AI Gap Analysis & Recommendations
    # ════════════════════════════════════════════════════════════════════════
    with col2:

        # ── Inferred Role + Domain badge ─────────────────────────────────────
        inferred_role = intelligence_data.get("inferred_role", "Unable to determine")
        domain        = intelligence_data.get("domain", "Unknown")
        st.markdown(f"""
        <div class="role-badge">
          <div class="role-label">🤖 AI-Inferred Career Path</div>
          <div class="role-value">{inferred_role}</div>
          <div class="domain-value">🌐 Domain: {domain}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Confidence Score ─────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="card-title">📊 Resume Confidence Score</div>', unsafe_allow_html=True)

            conf_score   = intelligence_data.get("confidence_score", 0)
            conf_just    = intelligence_data.get("confidence_justification", "")

            if conf_score >= 75:
                conf_label, bar_color = "High",   "#16a34a"
            elif conf_score >= 45:
                conf_label, bar_color = "Medium", "#d97706"
            else:
                conf_label, bar_color = "Low",    "#dc2626"

            st.markdown(f"""
            <div class="conf-row">
              <div class="conf-score-box">
                <div class="score" style="color:{bar_color}">{conf_score}</div>
                <div class="label">{conf_label}</div>
              </div>
              <div class="conf-just">{conf_just if conf_just else "No justification available."}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(conf_score / 100.0)


        # ── Critical Skill Gaps — amber alert ────────────────────────────────
        missing_skills = intelligence_data.get("missing_skills", [])
        with st.container(border=True):
            st.markdown('<div class="card-title">⚠️ Skill Gap Analysis</div>', unsafe_allow_html=True)

            if missing_skills and missing_skills != ["N/A"]:
                gaps_html = "".join(
                    f'<span class="gap-tag">⚡ {s}</span>' for s in missing_skills if s and s != "N/A"
                )
                st.markdown(f"""
                <div class="alert-amber">
                  <div class="alert-title">⚠ Critical Skill Gaps Detected for '{inferred_role}'</div>
                  <div style="line-height: 2.4;">{gaps_html}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success("✅ No critical skill gaps identified for the inferred role.")



        # ── DEET AI Recommendations — gray cards ─────────────────────────────
        actionable = intelligence_data.get("actionable_feedback", [])
        with st.container(border=True):
            st.markdown('<div class="card-title">🎯 DEET AI Recommendations</div>', unsafe_allow_html=True)

            if actionable:
                for i, tip in enumerate(actionable, 1):
                    if tip and tip != "N/A":
                        st.markdown(f"""
                        <div class="rec-card">
                          <span class="rec-num">{i}</span>{tip}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No recommendations available.")



    # ─── ACTION BUTTONS ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🚀 Finalise & Submit")

    final_output = {
        "resume_data":          resume_data,
        "intelligence_metadata": intelligence_data
    }
    json_string = json.dumps(final_output, indent=2)

    act_col1, act_col2 = st.columns([1, 1], gap="medium")

    with act_col1:
        if st.button("✅ Update Profile & Sync with State Registry", type="primary"):
            st.balloons()
            st.success("🎉 Profile submitted successfully to the Telangana DEET Employment Registry!")
            st.info("Your application is under review by the AI-powered job matching system.")

    with act_col2:
        st.download_button(
            label="⬇ Download Structured JSON Profile",
            data=json_string,
            file_name="deet_profile_structured.json",
            mime="application/json"
        )
