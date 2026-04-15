import logging


def speak(text: str):
    """Tenta usar pyttsx3; se não disponível, usa `espeak` como fallback."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return
    except Exception:
        logging.info("pyttsx3 não disponível ou falha; tentando espeak")
    # fallback
    try:
        import subprocess
        subprocess.run(["espeak", text], check=False)
    except Exception:
        logging.exception("Falha ao executar TTS")
