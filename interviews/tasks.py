# interviews/tasks.py
import logging
import json
from celery import shared_task
from django.db import transaction
from ai_services.llm import call_groq

logger = logging.getLogger(__name__)


def _generate_interview_questions(
    job_title: str,
    job_description: str,
    skills: list,
    total_experience: float = 0,
    experience_summary: str = ""
) -> list:
    """Generate 5 personalized interview questions using Groq."""
    experience_context = ""
    if total_experience > 0:
        experience_context += f"Candidate has {total_experience} years of total work experience. "
    if experience_summary:
        experience_context += f"Relevant experience summary: {experience_summary}"

    prompt = f"""
You are an HR interviewer for a {job_title} position.
Job description: {job_description}
Candidate skills: {', '.join(skills)}
{experience_context}

Generate EXACTLY 10 interview questions with the following structure:

- 2 introductory questions (very short, simple, ice-breaking)
- 3 basic questions (easy level, short, testing fundamental knowledge)
- 5 technical questions (medium difficulty, slightly detailed but still concise)

Guidelines:
- Keep all questions clear and concise (avoid long paragraphs)
- Tailor questions to the candidate's skills and experience level
- Mix technical and practical scenarios where appropriate
- Do not make questions overly complex or tricky

Return ONLY a JSON array of strings, no extra text.

Example:
["Q1", "Q2", ..., "Q10"]
"""
    response = call_groq(prompt, temperature=0.7)
    try:
        questions = json.loads(response.strip())
        if isinstance(questions, list):
            return questions[:10]  # prompt asks for 10 questions
    except json.JSONDecodeError:
        import re
        lines = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\Z)', response, re.DOTALL)
        if lines:
            return [l.strip() for l in lines[:5]]
    return [
        "Tell me about yourself.",
        "Why do you want this job?",
        "What are your strengths?",
        "Where do you see yourself in 5 years?",
        "Do you have any questions?"
    ]


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="interviews.generate_interview_questions_task",
)
def generate_interview_questions_task(self, application_id: str):
    """Generate questions for an application and create/update InterviewSession."""
    print(f"📋 [TASK] generate_interview_questions_task received for application {application_id}")
    from applications.models import Application
    from interviews.models import InterviewSession
    from resumes.models import Resume
    from accounts.models import CandidateProfile

    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        logger.error("Application not found: %s", application_id)
        return

    resume = application.resume
    skills = []
    total_exp = 0.0
    exp_summary = ""

    if resume and resume.parse_status == "PARSED":
        skills = resume.skills
        # Get candidate profile for total_experience
        profile = getattr(application.candidate, 'candidate_profile', None)
        if profile:
            total_exp = profile.total_experience or 0.0
        # Build experience summary
        if resume.experience:
            exp_items = []
            for exp in resume.experience[:3]:
                if isinstance(exp, dict):
                    exp_items.append(f"{exp.get('title', '')} at {exp.get('company', '')}")
                else:
                    exp_items.append(str(exp))
            exp_summary = "; ".join(exp_items)
    else:
        # Use job skills as fallback
        skills = application.job.skills_required
        if not skills:
            skills = ["communication", "teamwork", "problem-solving"]
        # Retry logic if resume not parsed
        if self.request.retries == 0:
            raise self.retry(countdown=60)
        else:
            logger.warning(f"Using fallback skills for application {application_id}")

    job = application.job
    questions = _generate_interview_questions(
        job.title,
        job.description,
        skills,
        total_experience=total_exp,
        experience_summary=exp_summary
    )

    with transaction.atomic():
        session, created = InterviewSession.objects.get_or_create(
            application=application,
            defaults={"generated_questions": questions}
        )
        if not created:
            session.generated_questions = questions
            session.save()

    logger.info("Interview questions generated for Application %s", application_id)