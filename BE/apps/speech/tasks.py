import base64

from celery import shared_task
from celery.signals import worker_ready


@shared_task(time_limit=60, soft_time_limit=50)
def assess_recording(audio_b64: str, text: str, language: str, pinyin: list | None = None) -> dict:
    """Runs in the Celery worker: the only process holding the 320 MB recogniser (settings.SPEECH_MODEL_PATH).
    Returns the result, or {"problem": code, "detail": message} for a recording that cannot be scored."""
    from .assess import AudioProblem, assess

    try:
        return assess(base64.b64decode(audio_b64), text, language, pinyin)
    except AudioProblem as e:
        return {"problem": e.code, "detail": e.message}


@worker_ready.connect
def _warm_up(**_):
    """Load the recogniser and espeak-ng when the worker starts, so the first learner does not wait for it."""
    from . import phonology, recognizer

    try:
        if recognizer.available():
            recognizer.get()
            phonology.expected_units("hello", "en")
    except Exception:  # noqa: BLE001 - scoring then answers "unavailable"; e-mails still go out
        pass
