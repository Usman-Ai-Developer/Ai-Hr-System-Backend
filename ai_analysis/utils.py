# ai_analysis/utils.py
import os
import subprocess
import logging
import cv2
import numpy as np
import whisper
from deepface import DeepFace
from ai_services.llm import call_groq


logger = logging.getLogger(__name__)

# Lazy-loaded on first call to speech_to_text().
# Loading at module level runs during Django/Celery boot — avoid it.
_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model (first use)...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def extract_audio(video_path: str) -> str:
    """
    Extract audio from video file, apply noise reduction and speech enhancement,
    and return path to cleaned WAV file.
    """
    audio_path = os.path.splitext(video_path)[0] + "_clean.wav"
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",                     # no video
        "-acodec", "pcm_s16le",    # 16-bit PCM
        "-ar", "16000",            # 16kHz sample rate
        "-ac", "1",                # mono
        "-af", (
            "highpass=f=80,"       # remove low-frequency rumble
            "lowpass=f=3000,"      # reduce high-frequency hiss
            "afftdn=nr=10:nf=-30," # noise reduction using FFT
            "loudnorm,"            # normalize loudness
            "volume=1.5"           # boost quiet audio
        ),
        "-y",                       # overwrite
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
    Extract frames from video, run emotion detection,
    and return a confidence score (0‑100) that penalises
    negative emotions (fear, sad, angry, disgust).
    DeepFace returns percentages (0‑100), so we map
    (positive% - negative%) directly to 0‑100.
    """
    import cv2
    import numpy as np
    from deepface import DeepFace

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Cannot open video: %s", video_path)
        return 50.0

    positive_emotions = ['happy', 'neutral', 'surprise']
    negative_emotions = ['fear', 'angry', 'sad', 'disgust']

    positive_sum = {e: 0.0 for e in positive_emotions}
    negative_sum = {e: 0.0 for e in negative_emotions}
    valid_detections = 0

    # Try to read up to 10 frames (no skipping, just sequential)
    for _ in range(10):
        ret, frame = cap.read()
        if not ret:
            break

        temp_img = f"{video_path}_frame_.jpg"
        cv2.imwrite(temp_img, frame)

        try:
            results = DeepFace.analyze(
                img_path=temp_img,
                actions=['emotion'],
                enforce_detection=False,
                silent=True,
                detector_backend='opencv',
            )
            if isinstance(results, list) and len(results) > 0:
                emotions = results[0]['emotion']
                for e in positive_emotions:
                    positive_sum[e] += emotions.get(e, 0)
                for e in negative_emotions:
                    negative_sum[e] += emotions.get(e, 0)
                valid_detections += 1
                logger.info("Frame emotions: %s", {k: f"{v:.1f}" for k, v in emotions.items()})
        except Exception as e:
            logger.warning("Frame analysis failed: %s", e)
        finally:
            if os.path.exists(temp_img):
                os.remove(temp_img)

    cap.release()

    if valid_detections == 0:
        return 50.0

    # Average the sums (percentages)
    avg_pos = sum(positive_sum.values()) / valid_detections
    avg_neg = sum(negative_sum.values()) / valid_detections
    raw = avg_pos - avg_neg  # range: -100 to +100

    # Map to 0‑100 (e.g. 0% positive, 100% negative -> 0 confidence;
    #                100% positive, 0% negative -> 100 confidence;
    #                equal -> 50)
    confidence = (raw + 100) / 2
    return round(max(0.0, min(100.0, confidence)), 1)
# ai_analysis/utils.py (add this function)

def correct_transcript(transcript: str) -> str:
    """Fix ASR errors and minor grammar issues using Groq."""
    if not transcript or transcript.startswith("[No transcript") or transcript.startswith("[Transcription failed"):
        return transcript  # keep placeholders unchanged
    prompt = f"""
Please correct any speech-to-text errors, punctuation, and minor grammar mistakes in the following interview answer.
Return ONLY the corrected text, no extra commentary.

Original: "{transcript}"
"""
    try:
        corrected = call_groq(prompt, temperature=0.1)
        return corrected.strip()
    except Exception as e:
        logger.error(f"Transcript correction failed: {e}")
        return transcript  # fallback to original