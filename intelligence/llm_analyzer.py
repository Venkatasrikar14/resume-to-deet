import json
import re
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Explicitly locate the .env file in the project root (parent of this file's directory)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are a Senior Technical Recruiter at Google and a Career Coach for the "
    "Telangana Government's DEET (Department of Employment Exchange and Training) program.\n\n"
    "Your job is to deeply analyze a candidate's resume, infer their strongest career path, "
    "and provide SPECIFIC, ACTIONABLE career guidance — never generic advice.\n\n"
    "CRITICAL RULES FOR actionable_feedback:\n"
    "- NEVER say generic things like 'Learn Python' or 'Improve communication skills'.\n"
    "- Instead, suggest SPECIFIC libraries, tools, projects, or certifications.\n"
    "  Examples:\n"
    "    * If they know Python → 'Build a FastAPI backend for your Resume project to demonstrate production-level API skills.'\n"
    "    * If they know React → 'Add server-side rendering with Next.js and deploy on Vercel to show full-stack capability.'\n"
    "    * If they're in Data Science → 'Publish a Kaggle notebook using XGBoost on a real-world dataset and link it on your resume.'\n"
    "    * If they're in Healthcare → 'Obtain BLS/ACLS certification and add patient outcome metrics to each role.'\n"
    "    * If they're in Culinary → 'Get FSSAI Food Safety Supervisor certification and document cost-saving menu optimizations.'\n\n"
    "You MUST output ONLY valid JSON. "
    "Absolutely no conversational filler, no markdown blocks, and no preamble.\n\n"
    "Fill in and return EXACTLY this JSON template — copy the structure, replace the values:\n"
    "{\n"
    '  "inferred_role": "string",\n'
    '  "domain": "string",\n'
    '  "skills": ["string", "string"],\n'
    '  "education": ["string", "string"],\n'
    '  "missing_skills": ["string", "string", "string"],\n'
    '  "confidence_score": 0,\n'
    '  "confidence_justification": "string",\n'
    '  "actionable_feedback": ["string", "string", "string"]\n'
    "}\n\n"
    "- Rule 1: If domain is IT/Tech, actionable_feedback MUST suggest specific frameworks, "
    "libraries, or portfolio projects (e.g., 'Deploy a CI/CD pipeline using GitHub Actions for your project').\n"
    "- Rule 2: If domain is Non-IT (e.g., Culinary, Healthcare, Finance), actionable_feedback MUST be "
    "hyper-specific to that field (e.g., 'Add NABH compliance experience' or 'Get CFA Level 1') "
    "and MUST NOT mention GitHub or coding.\n"
    "- Rule 3: All arrays must contain exactly 3 strings.\n"
    "- Rule 4: missing_skills should list skills the candidate does NOT have but NEEDS for the inferred_role. "
    "Be specific (e.g., 'Kubernetes orchestration' not just 'DevOps').\n"
    "- Rule 5: confidence_score (0-100) should reflect resume completeness, quantified achievements, "
    "and alignment with the inferred role."
)

FALLBACK = {
    "inferred_role": "Unable to determine",
    "domain": "Unknown",
    "skills": ["N/A"],
    "education": ["N/A"],
    "missing_skills": [
        "Domain-specific certification",
        "Quantified achievements",
        "Industry-standard tools",
    ],
    "confidence_score": 0,
    "confidence_justification": (
        "LLM analysis unavailable. "
        "Ensure GROQ_API_KEY is set in your .env file and you have network access."
    ),
    "actionable_feedback": [
        "Quantify your achievements with specific metrics relevant to your field.",
        "Ensure your contact information and professional credentials are clearly visible.",
        "Use strong action verbs and remove vague statements from your bullet points.",
    ],
}


def analyze_candidate_profile(raw_text: str, extracted_skills: list) -> dict:
    """
    Calls the Groq LLM and manually extracts a JSON block from the raw response.

    Returns a dict with keys:
        inferred_role            : str
        domain                   : str
        missing_skills           : list[str]  — exactly 3 items
        confidence_score         : int  (0–100)
        confidence_justification : str
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        fallback = FALLBACK.copy()
        fallback["confidence_justification"] = (
            "GROQ_API_KEY not found. Add it to your .env file as: GROQ_API_KEY=gsk_..."
        )
        return fallback

    try:
        client = Groq(api_key=api_key)

        truncated_text = raw_text[:4000] if raw_text else "(no resume text provided)"
        skills_str = ", ".join(extracted_skills) if extracted_skills else "None detected"

        user_message = (
            f"Resume Text:\n{truncated_text}\n\n"
            f"Extracted Skills (already present — do NOT include these in missing_skills): {skills_str}\n\n"
            "Return the JSON analysis object."
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=768,
        )

        raw_response = response.choices[0].message.content

        # ── Regex-extract the JSON block from raw text ────────────────────────
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in LLM response: {raw_response[:200]}")

        result = json.loads(match.group(0))

        # ── Unwrap array if LLM mistakenly wraps the object in [...] ──────────
        if isinstance(result, list):
            if result and isinstance(result[0], dict):
                result = result[0]
            else:
                raise ValueError(f"LLM returned a JSON array with no dict inside: {str(result)[:100]}")

        if not isinstance(result, dict):
            raise ValueError(f"LLM returned unexpected type {type(result).__name__}, expected dict.")

        # ── Validate required keys ────────────────────────────────────────────
        required_keys = {
            "inferred_role", "domain", "missing_skills",
            "confidence_score", "confidence_justification",
            "actionable_feedback",
        }
        missing_keys = required_keys - result.keys()
        if missing_keys:
            raise ValueError(f"LLM response missing keys: {missing_keys}")

        # ── Coerce and sanitize types ─────────────────────────────────────────
        result["confidence_score"] = max(0, min(100, int(result["confidence_score"])))

        if not isinstance(result["missing_skills"], list):
            result["missing_skills"] = [str(result["missing_skills"])]
        result["missing_skills"] = (result["missing_skills"] + ["N/A", "N/A", "N/A"])[:3]

        result["inferred_role"] = str(result.get("inferred_role", "Unknown"))
        result["domain"] = str(result.get("domain", "Unknown"))
        result["confidence_justification"] = str(result.get("confidence_justification", ""))

        if not isinstance(result["actionable_feedback"], list):
            result["actionable_feedback"] = [str(result["actionable_feedback"])]
        result["actionable_feedback"] = (
            result["actionable_feedback"] + ["Review your resume for clarity.", "N/A", "N/A"]
        )[:3]

        return result

    except json.JSONDecodeError as e:
        fallback = FALLBACK.copy()
        fallback["confidence_justification"] = f"JSON parse error: {str(e)[:100]}"
        return fallback

    except Exception as e:
        fallback = FALLBACK.copy()
        fallback["confidence_justification"] = f"LLM API error: {str(e)[:150]}"
        return fallback
