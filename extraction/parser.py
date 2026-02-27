import re
import json
import os
import pdfplumber  # type: ignore

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIGURATION — Edit these if Tesseract or Poppler are in a custom location
# ─────────────────────────────────────────────────────────────────────────────
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Path to Poppler's 'bin' folder (secondary fallback, only used if pymupdf fails).
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
POPPLER_PATH = r'C:\poppler\Library\bin'

# Minimum character count for pdfplumber's extracted text to be considered "good".
# If below this threshold, OCR fallback is triggered.
OCR_THRESHOLD = 50
# ─────────────────────────────────────────────────────────────────────────────

# ── Optional: pytesseract ─────────────────────────────────────────────────────
try:
    import pytesseract          # type: ignore
    from PIL import Image       # type: ignore
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None          # type: ignore
    Image = None                # type: ignore
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract/Pillow not installed. OCR disabled. "
        "Run: pip install pytesseract pillow")

# ── Optional: pymupdf (fitz) — renders PDF pages to images, NO Poppler needed ─
try:
    import fitz  # type: ignore  # pip install pymupdf
    FITZ_AVAILABLE = True
except ImportError:
    fitz = None  # type: ignore
    FITZ_AVAILABLE = False
    print("Warning: pymupdf not installed. Run: pip install pymupdf")

# ── Optional: pdf2image (secondary fallback, needs Poppler on Windows) ────────
try:
    from pdf2image import convert_from_path   # type: ignore
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    convert_from_path = None    # type: ignore
    PDF2IMAGE_AVAILABLE = False

# ── spaCy intentionally NOT imported ─────────────────────────────────────────
# spaCy's confection dependency crashes on Python 3.14 (pydantic v1 + re.Pattern
# incompatibility). The regex fallback in extract_personal_info() works fine.
nlp = None

from extraction.skills import extract_skills  # type: ignore


# ═════════════════════════════════════════════════════════════════════════════
# CORE TEXT EXTRACTION
# ═════════════════════════════════════════════════════════════════════════════

def extract_full_text(pdf_file_path: str) -> str:
    """
    Hybrid extraction pipeline for PDFs with EXTREME verbose debugging.
    """
    import traceback

    print("=" * 70)
    print("[DEBUG] extract_full_text() called")
    print(f"[DEBUG] Input file: {pdf_file_path}")
    print(f"[DEBUG] File exists: {os.path.exists(pdf_file_path)}")
    print(f"[DEBUG] TESSERACT_CMD: {TESSERACT_CMD}")
    print(f"[DEBUG]   -> Tesseract exists: {os.path.exists(TESSERACT_CMD)}")
    print(f"[DEBUG] POPPLER_PATH: {POPPLER_PATH}")
    print(f"[DEBUG]   -> Poppler path exists: {os.path.exists(POPPLER_PATH) if POPPLER_PATH else 'NOT SET'}")
    print(f"[DEBUG] PYTESSERACT_AVAILABLE: {PYTESSERACT_AVAILABLE}")
    print(f"[DEBUG] FITZ_AVAILABLE: {FITZ_AVAILABLE}")
    print(f"[DEBUG] PDF2IMAGE_AVAILABLE: {PDF2IMAGE_AVAILABLE}")
    print(f"[DEBUG] OCR_THRESHOLD: {OCR_THRESHOLD}")
    print("=" * 70)

    # ── Attempt 1: Digital text extraction (pdfplumber) ──────────────────
    print("\n[STEP 1] Attempting digital extraction with pdfplumber...")
    digital_text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                char_count = len(t) if t else 0
                print(f"  [pdfplumber] Page {i+1}: {char_count} chars")
                if t:
                    pages_text.append(t)
            digital_text = "\n".join(pages_text).strip()
    except Exception as e:
        print(f"  [pdfplumber ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()

    print(f"\n[STEP 1 RESULT] pdfplumber extracted {len(digital_text)} chars total")

    if len(digital_text) >= OCR_THRESHOLD:
        print(f"  -> PASS: {len(digital_text)} >= {OCR_THRESHOLD} threshold. Using digital text.")
        return digital_text

    print(f"  -> FAIL: {len(digital_text)} < {OCR_THRESHOLD} threshold. Need OCR.")

    # ── Pre-flight: Check if pytesseract is available ────────────────────
    if not PYTESSERACT_AVAILABLE:
        print("\n[FATAL] pytesseract not installed. Cannot do OCR.")
        print("  Fix: pip install pytesseract pillow")
        return digital_text or "DEBUG: OCR Failed - pytesseract not installed"

    # ── Attempt 2: pymupdf (fitz) + pytesseract ──────────────────────────
    print("\n[STEP 2] Attempting OCR with pymupdf (fitz) + pytesseract...")
    if FITZ_AVAILABLE:
        try:
            print("  OCR triggered for this file")
            pdf_doc = fitz.open(pdf_file_path)  # type: ignore[union-attr]
            page_count = len(pdf_doc)
            print(f"  [fitz] Opened PDF: {page_count} page(s)")

            ocr_pages = []
            from io import BytesIO
            for page_num in range(page_count):
                print(f"  [fitz] Rendering page {page_num + 1}/{page_count}...")
                page = pdf_doc[page_num]
                mat = fitz.Matrix(2, 2)  # type: ignore[union-attr]
                pix = page.get_pixmap(matrix=mat)
                print(f"    -> Pixmap: {pix.width}x{pix.height}")
                img_bytes = pix.tobytes("png")
                pil_img = Image.open(BytesIO(img_bytes))  # type: ignore[union-attr]
                print(f"    -> PIL Image: {pil_img.size}")
                print(f"    -> Running pytesseract.image_to_string...")
                page_text = pytesseract.image_to_string(pil_img)  # type: ignore[union-attr]
                char_count = len(page_text.strip())
                print(f"    -> OCR result: {char_count} chars")
                if page_text.strip():
                    ocr_pages.append(page_text.strip())

            pdf_doc.close()
            result = "\n".join(ocr_pages).strip()
            print(f"\n[STEP 2 RESULT] fitz OCR extracted {len(result)} chars from {len(ocr_pages)} page(s)")

            if result:
                print("  -> SUCCESS! Returning OCR text.")
                return result
            else:
                print("  -> WARNING: OCR ran but returned empty text. Tesseract may not recognize this content.")
        except Exception as e:
            print(f"\n  [fitz OCR ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            print("  -> Falling through to pdf2image...")
    else:
        print("  [SKIP] pymupdf not available.")

    # ── Attempt 3: pdf2image + pytesseract ────────────────────────────────
    print("\n[STEP 3] Attempting OCR with pdf2image + pytesseract...")
    if PDF2IMAGE_AVAILABLE:
        print(f"  [DEBUG] POPPLER_PATH = {POPPLER_PATH}")
        if POPPLER_PATH:
            poppler_exists = os.path.exists(POPPLER_PATH)
            print(f"  [DEBUG] os.path.exists(POPPLER_PATH) = {poppler_exists}")
            if not poppler_exists:
                print(f"  [WARNING] Poppler NOT found at: {POPPLER_PATH}")
                print(f"  Download from: https://github.com/oschwartz10612/poppler-windows/releases")
                print(f"  Extract and set POPPLER_PATH to the 'bin' folder.")
        else:
            print("  [DEBUG] POPPLER_PATH is None — pdf2image will search system PATH")

        try:
            print("  OCR triggered for this file (pdf2image)")
            convert_kwargs: dict = {"pdf_path": pdf_file_path}
            if POPPLER_PATH:
                convert_kwargs["poppler_path"] = POPPLER_PATH
            print(f"  [DEBUG] Calling convert_from_path with: {convert_kwargs}")
            images = convert_from_path(**convert_kwargs)  # type: ignore[operator]
            print(f"  [pdf2image] Converted to {len(images)} image(s)")

            ocr_pages = []
            for i, img in enumerate(images):
                print(f"  [pytesseract] Processing image {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(img)  # type: ignore[union-attr]
                char_count = len(page_text.strip())
                print(f"    -> OCR result: {char_count} chars")
                if page_text.strip():
                    ocr_pages.append(page_text.strip())

            result = "\n".join(ocr_pages).strip()
            print(f"\n[STEP 3 RESULT] pdf2image OCR extracted {len(result)} chars from {len(ocr_pages)} page(s)")
            if result:
                print("  -> SUCCESS!")
                return result
        except Exception as e:
            print(f"\n  [pdf2image OCR ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
    else:
        print("  [SKIP] pdf2image not available.")

    # ── FINAL FALLBACK ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("[FINAL FALLBACK] All extraction methods failed or returned empty.")
    print("  Check the logs above for the exact error.")
    print("=" * 70)
    return digital_text or "DEBUG: OCR Failed - Check Terminal for Error"


def extract_text_from_pdf(file) -> str:
    """
    Public wrapper used by app.py.
    Accepts a file path string or a file-like object.
    Routes through the hybrid extract_full_text pipeline.
    """
    path = file if isinstance(file, str) else getattr(file, "name", str(file))
    return extract_full_text(path)


def extract_text_from_image(file) -> str:
    """
    Extract text from a standalone image file (JPG, PNG, etc.) via Tesseract.
    """
    if not PYTESSERACT_AVAILABLE:
        print("OCR is disabled: pytesseract/Pillow not installed. "
              "Run: pip install pytesseract pillow")
        return json.dumps({"error": "pytesseract not installed. "
                                    "Run: pip install pytesseract pillow"})

    print("OCR triggered for this file")
    try:
        image = Image.open(file)                                # type: ignore[union-attr]
        text = pytesseract.image_to_string(image)              # type: ignore[union-attr]
        return text.strip()
    except pytesseract.TesseractNotFoundError:                 # type: ignore[union-attr]
        print("Error: Tesseract binary not found. "
              "Check TESSERACT_CMD path at the top of parser.py.")
        return json.dumps({"error": "Tesseract Engine not found. "
                                    "Please install Tesseract OCR."})
    except Exception as e:
        print(f"Error extracting text from image {file}: {e}")
        return json.dumps({"error": f"Image processing failed: {str(e)}"})


# ═════════════════════════════════════════════════════════════════════════════
# FIELD EXTRACTORS
# ═════════════════════════════════════════════════════════════════════════════

def extract_email(text: str) -> str:
    """Extracts email using regex."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    """Extracts a phone number (10+ digits) using regex."""
    pattern = r'(?:\+?\d{1,3}[-.\\s]?)?\(?\d{3}\)?[-.\\s]?\d{3}[-.\\s]?\d{4}'
    for match in re.finditer(pattern, text):
        phone = match.group(0)
        if len(re.sub(r'\D', '', phone)) >= 10:
            return phone
    return ""


def extract_links(text: str):
    """Extracts LinkedIn and GitHub/Portfolio URLs."""
    linkedin, github = "", ""
    urls = re.findall(r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9./~_-]+', text)
    simple = re.findall(r'(?:www\.)?(?:linkedin\.com|github\.com)[a-zA-Z0-9./~_-]+', text)
    for url in set(urls + simple):
        if "linkedin.com" in url.lower():
            linkedin = url
        elif "github.com" in url.lower() or "portfolio" in url.lower():
            github = url
    return linkedin, github


def extract_personal_info(text: str):
    """Extracts Full Name and Location using regex heuristics."""
    full_name, location, address = "", "", ""

    # Name: first short alphabetic-only line in the first few lines
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        if len(line.split()) <= 4 and re.match(r'^[A-Za-z\s]+$', line):
            full_name = line
            break

    # Location: look for labelled location or City, State pattern
    loc_match = re.search(r'(?i)(?:location|address|city)[:\s]+([A-Za-z ,]+)', text)
    if loc_match:
        location = loc_match.group(1).strip()

    return full_name, location, address


def extract_education(text: str) -> list:
    """Extracts education blocks: degree, specialization, institution, year, CGPA."""
    education_entities = []
    lines = text.split('\n')

    degree_pat = r'(?i)\b(B\.?Tech|B\.?E|M\.?Tech|MBA|B\.?Sc|M\.?Sc|Bachelor|Master)\b'
    year_pat   = r'\b(19|20)\d{2}\b'
    cgpa_pat   = r'(?:CGPA|GPA|Percentage)[\s:]*([0-9.]+)(?:/10|%)?'

    current_edu: dict = {}
    in_edu = False

    for i, line in enumerate(lines):
        ll = line.lower()
        if any(k in ll for k in ['education', 'academic background']):
            in_edu = True
            continue
        elif in_edu and any(k in ll for k in ['experience', 'skills', 'projects', 'certifications']):
            in_edu = False

        if in_edu or re.search(degree_pat, line):
            deg = re.search(degree_pat, line)
            if deg:
                if current_edu:
                    education_entities.append(current_edu)
                current_edu = {
                    "degree": deg.group(0).strip(),
                    "specialization": "",
                    "institution": "",
                    "year": "",
                    "cgpa": ""
                }
                ctx = " ".join(lines[i:i+3])
                yr = re.search(year_pat, line)
                if yr:
                    current_edu["year"] = yr.group(0)
                cgpa = re.search(cgpa_pat, ctx, re.IGNORECASE)
                if cgpa:
                    current_edu["cgpa"] = cgpa.group(1).strip()
                spec = re.search(
                    r'(?i)\b(Computer Science|CSE|IT|Mechanical|Electrical|ECE|Civil|Data Science)\b', ctx)
                if spec:
                    current_edu["specialization"] = spec.group(0).title()
                inst = re.search(
                    r'(?i)\b([A-Za-z\s]+(?:University|College|Institute|School|Academy|IIT|NIT))\b', ctx)
                if inst:
                    current_edu["institution"] = inst.group(0).strip()

    if current_edu:
        education_entities.append(current_edu)
    return education_entities


def extract_experience(text: str) -> list:
    """Extracts work experience entries: company, role, duration, description."""
    entities = []
    lines = text.split('\n')
    in_exp = False
    current: dict = {}
    desc_buf: list = []

    date_pat = (r'(?i)(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
                r' \d{4} - (?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
                r'[a-z]* \d{4}|Present)')

    for line in lines:
        ll = line.lower()
        if any(k in ll for k in ['experience', 'employment', 'work history']):
            if len(line.split()) < 4:
                in_exp = True
                continue
        if in_exp and any(k in ll for k in ['education', 'skills', 'projects', 'certifications']):
            if len(line.split()) < 3:
                in_exp = False
                if current:
                    current["description"] = "\n".join(desc_buf).strip()
                    entities.append(current)
                    current, desc_buf = {}, []
        if in_exp:
            dm = re.search(date_pat, line)
            if dm:
                if current:
                    current["description"] = "\n".join(desc_buf).strip()
                    entities.append(current)
                    desc_buf = []
                current = {"company": "", "role": "", "duration": dm.group(0), "description": ""}
                rest = line.replace(dm.group(0), "").strip()
                if rest:
                    parts = [p.strip() for p in rest.split('|') if p.strip()]
                    if len(parts) >= 2:
                        current["role"] = parts[0]
                        current["company"] = parts[1]
                    elif parts:
                        current["role"] = parts[0]
            elif current:
                desc_buf.append(line.strip())

    if current:
        current["description"] = "\n".join(desc_buf).strip()
        entities.append(current)
    return entities


# ═════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

def parse_resume(file) -> dict | str:
    """
    Main entry point.
    Accepts a PDF path, image path, or file-like object.
    Returns a structured dict, or a JSON error string on failure.
    """
    file_name = str(file).lower()

    if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
        text = extract_text_from_image(file)
        # extract_text_from_image returns a JSON error string on failure
        if isinstance(text, str) and text.startswith('{"error"'):
            return text
    else:
        text = extract_text_from_pdf(file)

    if not text or not text.strip():
        return json.dumps({"error": "Failed to extract text from document."})

    full_name, location, address = extract_personal_info(text)
    email    = extract_email(text)
    phone    = extract_phone(text)
    linkedin, github = extract_links(text)
    education  = extract_education(text)
    skills     = extract_skills(text)
    experience = extract_experience(text)

    return {
        "personal": {
            "full_name": full_name or "",
            "location":  location  or "",
            "address":   address   or ""
        },
        "contact": {
            "email":              email    or "",
            "phone":              phone    or "",
            "linkedin":           linkedin or "",
            "github_or_portfolio": github  or ""
        },
        "education":  education  if education  else [],
        "skills":     skills     if skills     else [],
        "experience": experience if experience else []
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_resume(sys.argv[1])
        print(json.dumps(result, indent=2))