from .llm_analyzer import analyze_candidate_profile


def run_intelligence(resume_json: dict, raw_text: str = "") -> dict:
    """
    Main intelligence entry point.

    Args:
        resume_json : structured dict returned by parse_resume()
        raw_text    : original PDF text (optional but improves LLM accuracy)

    Returns a dict with keys:
        inferred_role            : str
        domain                   : str
        missing_skills           : list[str]
        confidence_score         : int  (0–100)
        confidence_justification : str
    """
    skills = resume_json.get("skills", [])

    # If no raw text was provided, reconstruct a readable text block
    # from the structured resume data so the LLM has full context.
    if not raw_text:
        parts = []
        personal = resume_json.get("personal", {})
        contact = resume_json.get("contact", {})

        if personal.get("full_name"):
            parts.append(f"Name: {personal['full_name']}")
        if contact.get("email"):
            parts.append(f"Email: {contact['email']}")
        if contact.get("phone"):
            parts.append(f"Phone: {contact['phone']}")
        if contact.get("linkedin"):
            parts.append(f"LinkedIn: {contact['linkedin']}")
        if contact.get("github_or_portfolio"):
            parts.append(f"GitHub/Portfolio: {contact['github_or_portfolio']}")

        for edu in resume_json.get("education", []):
            parts.append(
                f"Education: {edu.get('degree', '')} in {edu.get('specialization', '')} "
                f"from {edu.get('institution', '')} ({edu.get('year', '')}), "
                f"CGPA: {edu.get('cgpa', 'N/A')}"
            )

        for exp in resume_json.get("experience", []):
            parts.append(
                f"Experience: {exp.get('role', '')} at {exp.get('company', '')} "
                f"[{exp.get('duration', '')}] — {exp.get('description', '')}"
            )

        parts.append(f"Skills: {', '.join(skills)}")
        raw_text = "\n".join(parts)

    return analyze_candidate_profile(raw_text, skills)
