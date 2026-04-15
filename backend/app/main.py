import os
import threading
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from .asr import ASR
from .wakeword import WakewordSimulator
from .nlu import parse_intent
from .tts import speak
from .homeassistant import HomeAssistantClient

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="JARVIS PoC")

# Componentes
asr = ASR(model_path=os.environ.get('VOSK_MODEL_PATH'))
wake = WakewordSimulator()
ha = HomeAssistantClient()

voice_thread = None
voice_running = False


def handle_command(text: str):
    logging.info("Texto reconhecido: %s", text)
    intent = parse_intent(text)
    logging.info("Intent parsed: %s", intent)
    # ação simples para exemplo
    if intent.get('intent') == 'turn_on' and intent.get('device') == 'light':
        # entity_id default (o usuário deve ajustar)
        entity = os.environ.get('DEFAULT_LIGHT_ENTITY', 'light.example')
        ha.turn_on(entity)
        resp = f"Ligando {entity}"
        speak(resp)
        return resp
    if intent.get('intent') == 'turn_off' and intent.get('device') == 'light':
        entity = os.environ.get('DEFAULT_LIGHT_ENTITY', 'light.example')
        ha.turn_off(entity)
        resp = f"Desligando {entity}"
        speak(resp)
        return resp
    if intent.get('intent') == 'status':
        resp = "Estou operacional."
        speak(resp)
        return resp
    # fallback
    resp = "Desculpe, não entendi."
    speak(resp)
    return resp


def _record_and_process(duration=5):
    try:
        import sounddevice as sd
        import soundfile as sf
        samplerate = 16000
        logging.info("Gravando audio por %ds...", duration)
        data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        tf = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(tf.name, data, samplerate)
        tf.close()
        text = asr.recognize_file(tf.name)
        try:
            os.unlink(tf.name)
        except Exception:
            pass
        if text:
            handle_command(text)
        else:
            logging.info('Nenhuma transcrição obtida')
    except Exception:
        logging.exception('Erro na gravação/processamento')


def _on_wake():
    logging.info('Wakeword acionado — escutando...')
    # grava 5s e processa
    _record_and_process(duration=5)


def _voice_loop():
    wake.start(_on_wake)


@app.post('/start')
async def start_loop():
    global voice_thread, voice_running
    if voice_running:
        return {"status": "already_running"}
    voice_running = True
    voice_thread = threading.Thread(target=_voice_loop, daemon=True)
    voice_thread.start()
    return {"status": "started"}


@app.post('/stop')
async def stop_loop():
    global voice_running
    if not voice_running:
        return {"status": "not_running"}
    wake.stop()
    voice_running = False
    return {"status": "stopped"}


@app.get('/health')
async def health():
    return {"status": "ok"}


class UploadResponse(BaseModel):
    text: str


@app.post('/recognize_file', response_model=UploadResponse)
async def recognize_file(file: UploadFile = File(...)):
    # grava para tmp e processa
    tf = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    content = await file.read()
    tf.write(content)
    tf.flush()
    tf.close()
    text = asr.recognize_file(tf.name)
    try:
        os.unlink(tf.name)
    except Exception:
        pass
    return {"text": text}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
