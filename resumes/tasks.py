# resumes/tasks.py
import logging
import json
import re
import pdfplumber
import os
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from ai_services.llm import call_groq, extract_json_from_llm_response

logger = logging.getLogger(__name__)


def _extract_pdf_text(file_path: str) -> str:
    """Extract raw text from PDF using pdfplumber."""
    try:
        text_pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_pages.append(text)
        return "\n".join(text_pages)
    except Exception as exc:
        logger.error("PDF extraction failed at %s: %s", file_path, exc)
        return ""


def _extract_phone_fallback(text: str) -> str:
    """Fallback regex to find phone numbers if LLM fails."""
    patterns = [
        r'\+?\d{1,4}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
        r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',
        r'\d{10,11}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().strip()
    return ""


def _parse_resume_with_llm(text: str) -> dict:
    """Send resume text to Groq and extract structured data."""
    prompt = f"""You are a resume parser. Extract information from the resume text and return ONLY a valid JSON object — no markdown, no code fences, no explanation.

The JSON must use exactly these keys:
{{
    "skills": ["skill1", "skill2"],
    "education": [{{"degree": "degree name", "institution": "university name", "year": "graduation year"}}],
    "experience": [{{"title": "job title", "company": "company name", "duration": "e.g. 2021-2023", "description": "brief summary"}}],
    "certifications": ["cert1", "cert2"],
    "languages": ["English", "Urdu"],
    "summary": "2-3 sentence professional summary",
    "total_experience": 2.5,
    "phone": "03001234567"
}}

Rules:
- skills: list every technical skill, tool, language, and framework mentioned
- education: list all degrees, diplomas, and courses
- experience: list all jobs and internships
- total_experience: total years of work experience as a decimal number (0.0 if fresher)
- phone: exact phone number string, or empty string "" if not found
- Return ONLY the JSON object. Do not wrap it in markdown or add any other text.

Resume text:
{text[:4000]}"""

    response = call_groq(prompt, temperature=0.1)
    logger.info(f"Groq raw response (first 500 chars): {response[:500]}")

    try:
        parsed = extract_json_from_llm_response(response)
    except Exception as e:
        logger.error(f"Failed to parse Groq JSON response: {e}\nRaw response: {response[:1000]}")
        raise Exception(f"LLM returned unparseable JSON: {e}")

    # Validate that critical fields are lists, not None or strings
    if not isinstance(parsed.get("skills"), list):
        logger.warning(f"LLM returned non-list skills: {parsed.get('skills')}")
        parsed["skills"] = []
    if not isinstance(parsed.get("education"), list):
        logger.warning(f"LLM returned non-list education: {parsed.get('education')}")
        parsed["education"] = []
    if not isinstance(parsed.get("experience"), list):
        logger.warning(f"LLM returned non-list experience: {parsed.get('experience')}")
        parsed["experience"] = []
    if not isinstance(parsed.get("certifications"), list):
        parsed["certifications"] = []
    if not isinstance(parsed.get("languages"), list):
        parsed["languages"] = []

    logger.info(
        f"Parsed resume: {len(parsed.get('skills', []))} skills, "
        f"{len(parsed.get('education', []))} education entries, "
        f"{len(parsed.get('experience', []))} experience entries"
    )
    return parsed
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="resumes.parse_resume_task",
)
def parse_resume_task(self, resume_id: str):
    """
    Parse resume PDF → extract structured data → update Resume model and CandidateProfile.
    Then DELETE the original PDF file.
    """
    from resumes.models import Resume
    from accounts.models import CandidateProfile
    from applications.models import Application
    from interviews.tasks import generate_interview_questions_task

    print(f"📄 [TASK] Starting parse_resume_task for resume ID: {resume_id}")

    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        print(f"❌ [TASK] Resume {resume_id} not found")
        logger.error("Resume %s not found", resume_id)
        return

    # Skip if already parsed
    if resume.parse_status == Resume.Status.PARSED:
        print(f"⏭️ [TASK] Resume {resume_id} already parsed, skipping")
        return

    # Update status to PARSING
    resume.parse_status = Resume.Status.PARSING
    resume.save(update_fields=["parse_status"])

    # Keep track of file path for deletion later
    pdf_path = resume.file.path if resume.file else None

    try:
        # 1. Extract raw text from PDF
        print(f"📄 [TASK] Extracting text from PDF: {pdf_path}")
        raw_text = _extract_pdf_text(pdf_path) if pdf_path else ""
        if not raw_text:
            raise Exception("Could not extract text from PDF")

        resume.raw_text = raw_text
        resume.save(update_fields=["raw_text"])
        print(f"📄 [TASK] Extracted {len(raw_text)} characters")

        # 2. Parse with LLM
        print(f"🤖 [TASK] Calling Groq for parsing...")
        parsed = _parse_resume_with_llm(raw_text)
        print(f"✅ [TASK] Groq response received")
        print(f"📞 LLM returned phone: '{parsed.get('phone')}'")

        # 3. Fallback for phone
        phone = parsed.get("phone")
        if not phone:
            phone = _extract_phone_fallback(raw_text)
            if phone:
                print(f"📞 Fallback phone extracted: '{phone}'")
            else:
                print("📞 No phone number found in resume text")
        else:
            print(f"📞 Using LLM phone: '{phone}'")

        with transaction.atomic():
            # 4. Update Resume Model
            resume.skills = parsed.get("skills", [])
            resume.education = parsed.get("education", [])
            resume.experience = parsed.get("experience", [])
            resume.certifications = parsed.get("certifications", [])
            resume.languages = parsed.get("languages", [])
            resume.parse_status = Resume.Status.PARSED
            resume.parsed_at = timezone.now()
            resume.save()

            # 5. Sync to CandidateProfile
            profile, _ = CandidateProfile.objects.get_or_create(user=resume.candidate)
            if parsed.get("summary"):
                profile.summary = parsed["summary"]
            if parsed.get("total_experience") is not None:
                profile.total_experience = float(parsed["total_experience"])
            if phone:
                profile.phone = phone
            profile.save()

        print(f"🎉 [TASK] Resume {resume_id} parsed successfully")

        # 6. ✅ DELETE the original PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"🗑️ [TASK] Deleted PDF: {pdf_path}")
                # Clear the file field to avoid broken links
                resume.file = None
                resume.save(update_fields=['file'])
            except Exception as e:
                logger.error(f"Failed to delete PDF {pdf_path}: {e}")

        # 7. Trigger pending interviews for this candidate using this resume
        pending_apps = Application.objects.filter(
            candidate=resume.candidate,
            resume=resume
        )
        for app in pending_apps:
            generate_interview_questions_task.delay(str(app.id))
            print(f"📋 [TASK] Triggered question generation for Application: {app.id}")

    except Exception as exc:
        print(f"❌ [TASK] Error parsing resume {resume_id}: {exc}")
        logger.exception("Unexpected error parsing resume %s", resume_id)
        resume.parse_status = Resume.Status.FAILED
        resume.parse_error = str(exc)
        resume.save()
        # Do NOT delete file on failure – keep for retry
        raise self.retry(exc=exc)

    return True