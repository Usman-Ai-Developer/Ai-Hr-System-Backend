# ai_analysis/utils.py
import os
import subprocess
import logging

# NOTE: cv2, numpy, whisper, DeepFace are NOT imported at module level.
# They are only imported inside the functions that use them.
# This keeps Django startup lightweight on the web server —
# these libraries are only needed in Celery worker tasks.

from ai_services.llm import call_groq

logger = logging.getLogger(__name__)

# Lazy-loaded Whisper model — only initialised on first transcription call.
_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper  # imported here, not at module level
        logger.info("Loading Whisper model (first use)...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def extract_audio(video_path: str) -> str:
    """
    Extract audio from video, apply noise reduction and normalisation,
    and return path to a cleaned 16kHz mono WAV file.
    """
    audio_path = os.path.splitext(video_path)[0] + "_clean.wav"
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-af", (
            "highpass=f=80,"
            "lowpass=f=3000,"
            "afftdn=nr=10:nf=-30,"
            "loudnorm,"
            "volume=1.5"
        ),
        "-y",
        audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return audio_path


def speech_to_text(audio_path: str) -> str:
    """Transcribe audio file using Whisper."""
    result = _get_whisper_model().transcribe(audio_path, language="en", task="transcribe")
    return result["text"]


def compute_facial_confidence(video_path: str) -> float:
    """
    Sample frames evenly across the video, run DeepFace emotion detection,
    and return a confidence score (0-100).
    Positive emotions (happy, neutral, surprise) raise the score;
    negative emotions (fear, angry, sad, disgust) lower it.
    """
    import cv2          # heavy — imported here only
    import numpy as np  # heavy — imported here only
    from deepface import DeepFace  # heavy — imported here only

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Cannot open video: %s", video_path)
        return 50.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_count = min(10, total_frames)
    if sample_count == 0:
        cap.release()
        return 50.0

    # Sample evenly across the full video duration
    indices = np.linspace(0, total_frames - 1, sample_count, dtype=int)

    positive_emotions = ['happy', 'neutral', 'surprise']
    negative_emotions = ['fear', 'angry', 'sad', 'disgust']
    positive_sum = {e: 0.0 for e in positive_emotions}
    negative_sum = {e: 0.0 for e in negative_emotions}
    valid_detections = 0

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if not ret:
            continue

        temp_img = f"{video_path}_frame_{idx}.jpg"
        cv2.imwrite(temp_img, frame)
        try:
            results = DeepFace.analyze(
                img_path=temp_img,
                actions=['emotion'],
                enforce_detection=False,
                silent=True,
                detector_backend='opencv',
            )
            if isinstance(results, list) and results:
                emotions = results[0]['emotion']
                for e in positive_emotions:
                    positive_sum[e] += emotions.get(e, 0)
                for e in negative_emotions:
                    negative_sum[e] += emotions.get(e, 0)
                valid_detections += 1
        except Exception as e:
            logger.warning("Frame %d analysis failed: %s", idx, e)
        finally:
            if os.path.exists(temp_img):
                os.remove(temp_img)

    cap.release()

    if valid_detections == 0:
        return 50.0

    avg_pos = sum(positive_sum.values()) / valid_detections
    avg_neg = sum(negative_sum.values()) / valid_detections
    raw = avg_pos - avg_neg          # -100 to +100
    confidence = (raw + 100) / 2    # map to 0-100
    return round(max(0.0, min(100.0, confidence)), 1)


def correct_transcript(transcript: str) -> str:
    """Fix ASR errors and minor grammar issues using Groq."""
    if not transcript or transcript.startswith("[No transcript") or transcript.startswith("[Transcription failed"):
        return transcript
    prompt = f"""Please correct any speech-to-text errors, punctuation, and minor grammar mistakes in the following interview answer.
Return ONLY the corrected text, no extra commentary.

Original: "{transcript}"
"""
    try:
        corrected = call_groq(prompt, temperature=0.1)
        return corrected.strip()
    except Exception as e:
        logger.error(f"Transcript correction failed: {e}")
        return transcript
