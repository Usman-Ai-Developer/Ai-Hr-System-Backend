# ai_analysis/tasks.py
import os
import tempfile
import logging
from celery import shared_task
from django.db import transaction
from django.db.models import Avg
from django.conf import settings
from ai_services.llm import call_groq, extract_json_from_llm_response

# NOTE: ai_analysis.utils is NOT imported at module level.
# It imports cv2/whisper/deepface which are not installed on the web server.
# All utils imports happen inside the task function body below.

from interviews.models import InterviewSession, InterviewAnswer
from .models import AIAnalysis

logger = logging.getLogger(__name__)


@shared_task(
    name="ai_analysis.evaluate_interview_from_file_task",
    bind=True,
    max_retries=2
)
def evaluate_interview_from_file_task(self, session_id: str):
    """
    Gather all Q&A, transcribe & correct videos, compute facial confidence,
    send to Groq, save analysis, and delete all video/audio files.
    Heavy ML imports (cv2, whisper, deepface) happen here — inside the task —
    so Django's web server startup never touches them.
    """
    # Import ML utilities here, not at module level
    from ai_analysis.utils import (
        extract_audio,
        speech_to_text,
        compute_facial_confidence,
        correct_transcript,
    )

    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        logger.error(f"Session {session_id} not found")
        return

    answers = InterviewAnswer.objects.filter(session=session).order_by('question_order')
    if not answers.exists():
        logger.warning(f"No answers for session {session_id}")
        return

    qa_lines = []
    for ans in answers:
        transcript = ans.transcript
        video_path = None
        audio_path = None

        if not transcript and ans.video_url:
            try:
                video_path = os.path.join(settings.MEDIA_ROOT, ans.video_url.name)
                logger.info(f"Processing video: {video_path}")
                if not os.path.exists(video_path):
                    transcript = "[Video file not found]"
                else:
                    audio_path = extract_audio(video_path)
                    logger.info(f"Audio extracted to: {audio_path}")
                    raw_transcript = speech_to_text(audio_path)
                    logger.info(f"Raw transcription length: {len(raw_transcript)}")
                    transcript = correct_transcript(raw_transcript)
                    logger.info(f"Corrected transcription length: {len(transcript)}")
                    ans.transcript = transcript
                    ans.save(update_fields=['transcript'])

                    confidence = compute_facial_confidence(video_path)
                    logger.info(f"Facial confidence: {confidence}")
                    ans.confidence_score = confidence
                    ans.save(update_fields=['confidence_score'])

            except Exception as e:
                logger.exception(f"Processing failed for answer {ans.id}: {e}")
                transcript = "[Processing failed]"
            finally:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Deleted audio file: {audio_path}")

        elif not transcript:
            transcript = "[No transcript available]"

        qa_lines.append(f"Question {ans.question_order}: {ans.question_text}")
        qa_lines.append(f"Answer: {transcript}")
        qa_lines.append("")

        # Delete original video file after processing
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                logger.info(f"Deleted video file: {video_path}")
                ans.video_url = None
                ans.save(update_fields=['video_url'])
            except Exception as e:
                logger.error(f"Failed to delete video {video_path}: {e}")

    qa_text = "\n".join(qa_lines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(qa_text)
        temp_path = f.name

    try:
        prompt = f"""You are an AI HR evaluator. Below is a complete interview transcript.
Analyze the candidate's answers and provide a JSON response with:
- overall technical score (0-100)
- communication score (0-100)
- english proficiency score (0-100)
- relevance score (0-100)
- key strengths (string)
- areas for improvement (string)
- brief summary (string)
- constructive feedback for candidate (string)

Interview transcript:
{qa_text[:4000]}

Return ONLY valid JSON with these exact keys:
{{
    "technical_score": int,
    "communication_score": int,
    "english_score": int,
    "relevance_score": int,
    "strengths": "strengths text",
    "weaknesses": "weaknesses text",
    "summary": "summary text",
    "feedback": "feedback text"
}}
Please don't be too strict on scoring.
"""
        response = call_groq(prompt, temperature=0.3)
        logger.info(f"Groq response for session {session_id}: {response[:200]}...")

        try:
            result = extract_json_from_llm_response(response)
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            result = {
                "technical_score": 0,
                "communication_score": 0,
                "english_score": 0,
                "relevance_score": 0,
                "strengths": "Analysis failed.",
                "weaknesses": "Analysis failed.",
                "summary": "Could not generate analysis.",
                "feedback": "Please try again later."
            }

        avg_facial_confidence = answers.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 50.0

        with transaction.atomic():
            analysis, _ = AIAnalysis.objects.get_or_create(interview=session)
            analysis.technical_score      = result.get("technical_score", 0)
            analysis.communication_score  = result.get("communication_score", 0)
            analysis.avg_english_score    = result.get("english_score", 0)
            analysis.avg_relevance_score  = result.get("relevance_score", 0)
            analysis.confidence_score     = avg_facial_confidence
            analysis.strengths            = result.get("strengths", "")
            analysis.weaknesses           = result.get("weaknesses", "")
            analysis.overall_summary      = result.get("summary", "")
            analysis.candidate_feedback   = result.get("feedback", "")
            analysis.detailed_breakdown   = {
                "per_question": [
                    {
                        "question": ans.question_text,
                        "transcript": ans.transcript or "[No transcript]",
                    } for ans in answers
                ]
            }
            analysis.status = 'shortlisted' if analysis.technical_score >= 70 else 'pending'
            analysis.save()

            application = session.application
            overall = (
                analysis.technical_score +
                analysis.communication_score +
                analysis.avg_english_score +
                analysis.avg_relevance_score +
                analysis.confidence_score
            ) / 5
            application.ai_score = round(overall)
            application.save(update_fields=['ai_score'])

        logger.info(f"Analysis saved for session {session_id}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"Temporary file deleted: {temp_path}")
