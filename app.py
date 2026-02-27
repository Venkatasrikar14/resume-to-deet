import streamlit as st
import json
from extraction.parser import parse_resume, extract_text_from_pdf, extract_text_from_image
from intelligence import run_intelligence

# 1. Page Layout setup
st.set_page_config(page_title="IRIE - Resume to DEET", page_icon="⚡", layout="wide")

# Custom CSS for better spacing and modern look
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    .stDownloadButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    .css-1v0mbdj.etr89bj1 {
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 2rem;
        background-color: var(--background-color);
    }
    .skill-tag {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 12px;
        border-radius: 16px;
        margin: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .dark-skill-tag {
        display: inline-block;
        background-color: #1e3a8a;
        color: #bfdbfe;
        padding: 4px 12px;
        border-radius: 16px;
        margin: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .missing-skill {
        color: #ef4444;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Top Hero Section
st.title("AI-Powered Resume to DEET Profile Automation ⚡")
st.markdown("### Upload your resume. Auto-fill your profile. Analyze career readiness.")
st.divider()

# 3. Resume Upload Section
with st.container():
    st.markdown("#### 📄 Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, JPG, or PNG) to auto-extract details",
        type=["pdf", "jpg", "jpeg", "png"]
    )

if uploaded_file is not None:
    with st.spinner("Extracting data and running AI intelligence analysis..."):
        # Preserve original file extension so parse_resume routes correctly
        import os
        original_ext = os.path.splitext(uploaded_file.name)[1].lower() or ".pdf"
        temp_path = f"temp_resume{original_ext}"

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract raw text first (used by LLM for deeper context)
        if original_ext in [".jpg", ".jpeg", ".png"]:
            raw_text = extract_text_from_image(temp_path)
            if isinstance(raw_text, str) and raw_text.startswith('{"error"'):
                raw_text = ""  # OCR failed, continue with empty text
        else:
            raw_text = extract_text_from_pdf(temp_path)

        resume_data = parse_resume(temp_path)

        if isinstance(resume_data, str) and "error" in resume_data:
            st.error("Failed to parse the PDF. Please try a different file.")
            st.stop()

        intelligence_data = run_intelligence(resume_data, raw_text)

        # ── Merge LLM data into resume_data as fallback ───────────────────────
        # Skills: use LLM-extracted list when parser found nothing
        if not resume_data.get("skills"):
            resume_data["skills"] = intelligence_data.get("skills", [])

        # Education: LLM returns flat strings; convert to the dict shape the UI expects
        if not resume_data.get("education"):
            llm_edu = intelligence_data.get("education", [])
            if llm_edu and llm_edu != ["N/A"]:
                resume_data["education"] = [
                    {"degree": edu, "specialization": "", "institution": "", "year": "", "cgpa": ""}
                    for edu in llm_edu if edu
                ]

    st.success("✅ Profile extracted successfully!")
    st.divider()
    
    # 4. Auto-Filled Editable Profile Form
    st.header("✨ Auto-Filled DEET Profile")
    st.markdown("Review and edit your extracted details below before submission.")
    
    with st.container():
        col_p, col_c = st.columns(2, gap="large")
        
        with col_p:
            st.subheader("🔹 Personal Information")
            personal = resume_data.get("personal", {})
            full_name = st.text_input("Full Name", value=personal.get("full_name", ""))
            location = st.text_input("Location", value=personal.get("location", ""))
            address = st.text_area("Address", value=personal.get("address", ""), height=100)
            
            resume_data["personal"] = {
                "full_name": full_name,
                "location": location,
                "address": address
            }
            
        with col_c:
            st.subheader("🔹 Contact Information")
            contact = resume_data.get("contact", {})
            email = st.text_input("Email", value=contact.get("email", ""))
            phone = st.text_input("Phone", value=contact.get("phone", ""))
            linkedin = st.text_input("LinkedIn", value=contact.get("linkedin", ""))
            github = st.text_input("GitHub / Portfolio", value=contact.get("github_or_portfolio", ""))
            
            resume_data["contact"] = {
                "email": email,
                "phone": phone,
                "linkedin": linkedin,
                "github_or_portfolio": github
            }

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container():
        st.subheader("🔹 Education")
        education_list = resume_data.get("education", [])
        updated_education = []
        
        if not education_list:
            st.info("No education details found.")
        else:
            for i, edu in enumerate(education_list):
                with st.expander(f"🎓 Degree {i+1} : {edu.get('degree', 'Unknown')}", expanded=True):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        degree = st.text_input("Degree", value=edu.get("degree", ""), key=f"edu_deg_{i}")
                        spec = st.text_input("Specialization", value=edu.get("specialization", ""), key=f"edu_spec_{i}")
                        inst = st.text_input("Institution", value=edu.get("institution", ""), key=f"edu_inst_{i}")
                    with col_e2:
                        year = st.text_input("Year", value=edu.get("year", ""), key=f"edu_year_{i}")
                        cgpa = st.text_input("CGPA", value=edu.get("cgpa", ""), key=f"edu_cgpa_{i}")
                    
                    updated_education.append({
                        "degree": degree,
                        "specialization": spec,
                        "institution": inst,
                        "year": year,
                        "cgpa": cgpa
                    })
        resume_data["education"] = updated_education

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container():
        st.subheader("🔹 Skills")
        skills = resume_data.get("skills", [])
        
        # Display skills visually if they exist
        if skills:
            # Check theme approximately (Streamlit doesn't expose native dark mode check easily, using generic tag class)
            tags_html = "".join([f'<span class="skill-tag">{s}</span>' for s in skills if s])
            st.markdown(f"<div>{tags_html}</div><br>", unsafe_allow_html=True)
            
        skills_str = ", ".join(skills)
        updated_skills_str = st.text_area("Edit Skills (Comma separated)", value=skills_str)
        resume_data["skills"] = [s.strip() for s in updated_skills_str.split(",") if s.strip()]

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container():
        st.subheader("🔹 Experience")
        experience_list = resume_data.get("experience", [])
        updated_experience = []
        
        if not experience_list:
            st.info("No experience details found.")
        else:
            for i, exp in enumerate(experience_list):
                with st.expander(f"💼 Experience {i+1} : {exp.get('role', 'Role')} at {exp.get('company', 'Company')}", expanded=True):
                    col_x1, col_x2 = st.columns(2)
                    with col_x1:
                        company = st.text_input("Company", value=exp.get("company", ""), key=f"exp_comp_{i}")
                        role = st.text_input("Role", value=exp.get("role", ""), key=f"exp_role_{i}")
                    with col_x2:
                        duration = st.text_input("Duration", value=exp.get("duration", ""), key=f"exp_dur_{i}")
                    
                    description = st.text_area("Description", value=exp.get("description", ""), height=100, key=f"exp_desc_{i}")
                    
                    updated_experience.append({
                        "company": company,
                        "role": role,
                        "duration": duration,
                        "description": description
                    })
        resume_data["experience"] = updated_experience

    st.divider()

    # 5. Intelligence Insights Section — powered by Groq LLM
    st.header("🧠 AI Career Insights")

    # ── Row 1: Inferred Role + Domain ───────────────────────────────────────
    r_col1, r_col2 = st.columns(2, gap="large")
    with r_col1:
        inferred_role = intelligence_data.get("inferred_role", "Unable to determine")
        st.markdown(
            f"<div style='padding:1rem;border-radius:10px;background:#f0fdf4;border:1.5px solid #16a34a'>"
            f"<p style='margin:0;color:#15803d;font-size:0.8rem;font-weight:600'>✅ RECOMMENDED ROLE</p>"
            f"<p style='margin:4px 0 0;font-size:1.3rem;font-weight:700;color:#111827'>{inferred_role}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
    with r_col2:
        domain = intelligence_data.get("domain", "Unknown")
        st.markdown(
            f"<div style='padding:1rem;border-radius:10px;background:#eff6ff;border:1.5px solid #3b82f6'>"
            f"<p style='margin:0;color:#1d4ed8;font-size:0.8rem;font-weight:600'>🌐 PRIMARY DOMAIN</p>"
            f"<p style='margin:4px 0 0;font-size:1.3rem;font-weight:700;color:#111827'>{domain}</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 2: Missing Skills ────────────────────────────────────────────
    st.subheader("🎯 Skill Gap Analysis")
    missing_skills = intelligence_data.get("missing_skills", [])
    if missing_skills:
    
        ms_cols = st.columns(len(missing_skills))
        for i, skill in enumerate(missing_skills):
            with ms_cols[i]:
                st.markdown(
                    f"<div style='text-align:center;padding:0.75rem;border-radius:8px;"
                    f"background:#fef2f2;border:1.5px solid #ef4444'>"
                    f"<span style='color:#dc2626;font-weight:600'>⚠ {skill}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    else:
        st.success("✅ No critical skill gaps identified for this role.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 3: Confidence Level + Justification ──────────────────────────
    st.subheader("📊 Resume Confidence Level")
    conf_score = intelligence_data.get("confidence_score", 0)
    conf_justification = intelligence_data.get("confidence_justification", "")

    if conf_score >= 75:
        conf_label, label_color = "High", "#16a34a"
    elif conf_score >= 45:
        conf_label, label_color = "Medium", "#d97706"
    else:
        conf_label, label_color = "Low", "#dc2626"

    c_col1, c_col2 = st.columns([1, 3])
    with c_col1:
        st.markdown(
            f"<div style='text-align:center;padding:1rem;border-radius:12px;"
            f"background:{label_color}20;border:2px solid {label_color}'>"
            f"<span style='font-size:2rem;font-weight:bold;color:{label_color}'>{conf_score}</span>"
            f"<br><span style='color:{label_color};font-weight:600'>{conf_label}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    with c_col2:
        st.progress(conf_score / 100.0)
        st.markdown("**Confidence Justification:**")
        if conf_justification:
            st.info(conf_justification)
        else:
            st.markdown("No justification data available.")

    st.divider()

    # 6. Action Buttons Container
    st.markdown("### 🚀 Finalize")
    b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
    
    # Prepare JSON data
    final_output = {
        "resume_data": resume_data,
        "intelligence_metadata": intelligence_data
    }
    json_string = json.dumps(final_output, indent=2)
    
    with b_col1:
        if st.button("Submit to DEET (Demo)", type="primary"):
            st.balloons()
            st.success("Profile submitted successfully to DEET Registration Database!")
            st.info("Your application is now under review by AI matching.")
            
    with b_col2:
        st.download_button(
            label="Download JSON Profile",
            data=json_string,
            file_name="deet_profile_structured.json",
            mime="application/json"
        )
