import re
from typing import List

def extract_resume_summary(text: str) -> str:
    """
    Extracts key skills and project-oriented sentences from raw resume text
    using regex heuristics. This avoids an extra LLM call, keeping token usage minimal.
    """
    if not text:
        return ""

    # Common technical terms to extract
    tech_keywords = [
        "python", "javascript", "typescript", "java", "c\\+\\+", "c#", "golang", "go", "rust", "ruby", "php",
        "html", "css", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "fastapi", "django", "flask",
        "react", "vue", "angular", "next.js", "node.js", "node", "express", "spring", "docker", "kubernetes",
        "aws", "gcp", "azure", "git", "ci/cd", "machine learning", "pytorch", "tensorflow", "pandas", "numpy",
        "rest api", "graphql", "kubernetes", "microservices", "agile", "scrum", "jenkins", "terraform"
    ]

    found_skills = []
    text_lower = text.lower()
    for skill in tech_keywords:
        # Match word boundaries to prevent matching "go" inside "good" or "c" inside "cat"
        pattern = r"\b" + skill + r"\b"
        if re.search(pattern, text_lower):
            # Normalize display capitalization
            display_skill = skill
            if skill in ["aws", "gcp", "sql", "nosql", "html", "css", "ci/cd", "rest api", "api"]:
                display_skill = skill.upper()
            elif skill in ["next.js", "node.js"]:
                display_skill = skill.title()
            elif skill == "c\\+\\+":
                display_skill = "C++"
            else:
                display_skill = skill.title()
            if display_skill not in found_skills:
                found_skills.append(display_skill)

    # Search for project or experience highlight sentences
    projects = []
    sentences = re.split(r"[.!?\n]+", text)
    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue
        # Heuristic keywords for projects or achievements
        if re.search(r"\b(project|built|developed|implemented|designed|created|led|optimized|achieved)\b", s_clean, re.IGNORECASE):
            if 15 < len(s_clean) < 150:
                projects.append(s_clean)
                if len(projects) >= 4:
                    break

    summary_parts = []
    if found_skills:
        summary_parts.append(f"Skills: {', '.join(found_skills)}")
    if projects:
        summary_parts.append("Key Projects & Experience:")
        for proj in projects:
            summary_parts.append(f"- {proj}")

    if not summary_parts:
        return text[:400].strip()  # fallback to first 400 chars of resume if no indicators found

    return "\n".join(summary_parts)
