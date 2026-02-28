import re
import json

# Predefined list of skills to look for
SKILLS_LIST = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "React", "Angular", "Vue", 
    "Node.js", "Django", "Flask", "Spring Boot", "SQL", "MySQL", "PostgreSQL", "MongoDB", 
    "Redis", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "Machine Learning", 
    "Deep Learning", "Data Science", "Pandas", "NumPy", "TensorFlow", "PyTorch", "NLP", "HTML", "CSS"
]

def extract_skills(text):
    """
    Extracts skills based on a predefined list.
    Case-insensitive matching.
    """
    found_skills = []
    text_lower = text.lower()
    for skill in SKILLS_LIST:
        # Use regex border matching to find exact words, avoiding partial matches where possible
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
            
    # As a fallback for non-boundary matches inside symbols like C++, C#
    for special_skill in ["C++", "C#"]:
        if special_skill.lower() in text_lower and special_skill not in found_skills:
            found_skills.append(special_skill)
            
    return sorted(list(set(found_skills)))
