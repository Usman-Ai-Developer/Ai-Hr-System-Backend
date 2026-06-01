import pdfplumber
import re
import json

PDF_PATH = r"D:\Developement\FYP 2\ai_hr_system\media\resumes\Muhammad_Ahmad_CV_1GuJxCY.pdf"
OUTPUT_FILE = r"D:\Developement\FYP 2\ai_hr_system\resumes\clean_resume.json"

def extract_text(file_path):
    full_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            width = page.width
            # Split the page to handle the two-column layout
            left_col = page.crop((0, 0, width * 0.45, page.height)).extract_text() or ""
            right_col = page.crop((width * 0.45, 0, width, page.height)).extract_text() or ""
            full_text += left_col + "\n" + right_col + "\n"
    return full_text

def clean_line(line):
    if not line: return None
    line = line.strip()
    # Updated to keep content even if it has a percentage, 
    # but still filters out solo percentage lines
    if re.match(r'^\d+%$', line): return None
    return line

def extract_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # Added "About Me" to the exclusion list
    ignore = ["python developer", "about me", "seo specialist", "resume", "cv"]
    
    for line in lines[:8]:
        if line.lower() in ignore: continue
        # Names are usually 2-3 words and alphabetic
        if 2 <= len(line.split()) <= 3 and re.match(r'^[A-Za-z\s]+$', line):
            return line.title()
    return "Not Found"

def extract_section(text, keyword, stop_headers):
    # Regex that stops when it hits any of the other section headers
    pattern = rf"{keyword}\s*:?\s*(.*?)(?=\n\s*(?:{'|'.join(stop_headers)})|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match: return []
    
    return [clean_line(l) for l in match.group(1).split("\n") if clean_line(l)]

def build_resume(text):
    # Define common headers to use as anchors/stoppers
    headers = ["Education", "Experience", "Soft Skills", "Language", "About Me", "Professional Experience"]
    
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\d{10,11})', text)
    
    skills_db = ["python", "ai", "seo", "project management", "excel", "word", "powerpoint", "data entry"]
    found_skills = [s for s in skills_db if s in text.lower()]

    return {
        "name": extract_name(text),
        "email": email.group() if email else "Not Found",
        "phone": phone.group() if phone else "Not Found",
        "skills": found_skills,
        "education": extract_section(text, "Education", headers),
        "experience": extract_section(text, "Professional Experience", headers),
        # If 'Soft Skills' contains percentages you want to remove, you can add a regex filter here
        "soft_skills": extract_section(text, "Soft Skills", headers)
    }

if __name__ == "__main__":
    raw_text = extract_text(PDF_PATH)
    structured = build_resume(raw_text)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=4)
    print("✅ Extraction Complete.")