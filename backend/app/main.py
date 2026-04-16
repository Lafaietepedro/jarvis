import os
import threading
import tempfile
import logging
from typing import Any

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from .asr import ASR
from .core import JarvisCore
from .diagnostics import collect_diagnostics
from .presence import build_greeting, build_presence
from .wakeword import WakewordSimulator
from .tts import speak

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="JARVIS PoC")

# Componentes
asr = ASR(model_path=os.environ.get('VOSK_MODEL_PATH'))
wake = WakewordSimulator()
jarvis = JarvisCore()

voice_thread = None
voice_running = False


def _speak_async(text: str):
    threading.Thread(target=speak, args=(text,), daemon=True).start()


def execute_command(
    text: str,
    speak_response: bool = True,
    confirm_actions: bool = False,
    private: bool = False,
    source: str = "text",
):
    result = jarvis.execute(
        text,
        options={"confirm_actions": confirm_actions, "private": private, "source": source},
    )
    if speak_response:
        speak(result["response"])
    return result


def handle_command(text: str):
    result = execute_command(text, speak_response=True, source="voice")
    return result["response"]


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
    jarvis.session_state.set_processing(current_task="voice_command")
    # grava 5s e processa
    _record_and_process(duration=5)


def _voice_loop():
    wake.start(_on_wake)


@app.post('/start')
async def start_loop():
    global voice_thread, voice_running
    context = jarvis.context_provider.get_context()
    greeting = build_greeting(context, mode="voice")
    if voice_running:
        return {"status": "already_running", "greeting": greeting, "voice_listening": True}
    voice_running = True
    jarvis.session_state.set_listening()
    voice_thread = threading.Thread(target=_voice_loop, daemon=True)
    voice_thread.start()
    _speak_async(greeting)
    return {"status": "started", "greeting": greeting, "voice_listening": True}


@app.post('/stop')
async def stop_loop():
    global voice_running
    if not voice_running:
        return {"status": "not_running"}
    wake.stop()
    voice_running = False
    jarvis.session_state.set_active()
    return {"status": "stopped"}


@app.post('/pause')
async def pause():
    global voice_running
    if voice_running:
        wake.stop()
        voice_running = False
    jarvis.session_state.set_paused()
    return {"status": "paused"}


@app.post('/resume')
async def resume():
    jarvis.session_state.set_active()
    return {"status": "active"}


@app.get('/health')
async def health():
    return {"status": "ok"}


class UploadResponse(BaseModel):
    text: str


class CommandRequest(BaseModel):
    text: str
    speak_response: bool = False
    confirm_actions: bool = False
    private: bool = False


class ClearHistoryRequest(BaseModel):
    confirm: bool = False


class CommandResponse(BaseModel):
    text: str
    intent: dict[str, Any]
    response: str
    action: dict[str, Any]
    suggestions: list[str]
    context: dict[str, Any]
    data: dict[str, Any]
    session: dict[str, Any]


class ContextResponse(BaseModel):
    project: dict[str, Any]
    privacy: dict[str, Any]


class PresenceResponse(BaseModel):
    status: str
    name: str
    mode: str
    greeting: str
    voice_listening: bool
    uptime_seconds: int
    started_at: str
    last_activity_at: str
    current_task: str | None
    automation_checkpoints: list[dict[str, Any]]
    privacy: dict[str, Any]
    project: dict[str, Any]
    suggestions: list[str]


@app.get('/', response_model=PresenceResponse)
async def root():
    context = jarvis.context_provider.get_context()
    return build_presence(context, session=jarvis.session_state.snapshot(), mode="text")


@app.get('/presence', response_model=PresenceResponse)
async def presence():
    context = jarvis.context_provider.get_context()
    return build_presence(context, session=jarvis.session_state.snapshot(), mode="text")


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


@app.post('/command', response_model=CommandResponse)
async def command(payload: CommandRequest):
    return execute_command(
        payload.text,
        speak_response=payload.speak_response,
        confirm_actions=payload.confirm_actions,
        private=payload.private,
    )


@app.get('/context', response_model=ContextResponse)
async def context():
    return jarvis.context_provider.get_context()


@app.get('/history')
async def history(limit: int = 10):
    return {"commands": jarvis.memory_store.recent_commands(limit=limit)}


@app.get('/history/export')
async def export_history(limit: int | None = None):
    return jarvis.memory_store.export_history(limit=limit)


@app.post('/history/clear')
async def clear_history(payload: ClearHistoryRequest):
    if not payload.confirm:
        return {"status": "needs_confirmation", "reason": "confirmation_required"}
    deleted = jarvis.memory_store.clear_history()
    return {"status": "done", "deleted": deleted}


@app.get('/privacy')
async def privacy():
    return jarvis.execute("painel de privacidade", options={"private": True})


@app.get('/diagnostics')
async def diagnostics():
    return collect_diagnostics(jarvis.context_provider.get_context())


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
