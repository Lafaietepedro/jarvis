# J.A.R.V.I.S. — PoC (Offline-first)

Projeto inicial para um assistente multimodal estilo J.A.R.V.I.S., offline-first com opção híbrida.

Visão rápida
- Wake-word (simulado)
- ASR: Vosk (local)
- NLU: rule-based simples
- Integração: Home Assistant (REST)
- TTS: pyttsx3 / espeak fallback

Pré-requisitos (desenvolvimento)
- Python 3.11+
- Linux (Intel NUC recomendado) com audio input/output configurado
- Vosk model (baixe e extraia, defina `VOSK_MODEL_PATH`)

Como rodar localmente (rápido)

```bash
# Entrar na pasta backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Defina o caminho do modelo Vosk (baixe um modelo 16kHz)
export VOSK_MODEL_PATH=/caminho/para/model

# Opcional: configurar Home Assistant (se for usar)
export HOME_ASSISTANT_URL=http://seu-ha.local:8123
export HOME_ASSISTANT_TOKEN=SEU_LONG_LIVED_ACCESS_TOKEN

# Rodar em desenvolvimento
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints úteis
- `GET /health` — healthcheck
- `POST /start` — inicia loop de wake+listen (simulado wake)
- `POST /stop` — para loop
- `POST /recognize_file` — faz upload de WAV e retorna transcrição

Notas
- Este PoC usa um simulador de wake-word por simplicidade. Substitua por Porcupine/Precise quando estiver pronto.
- Baixe modelos Vosk apropriados e defina `VOSK_MODEL_PATH`.

Roadmap curto: integrar LLM local (LLama2 quantizado), visão (YOLOv8) e skills plugáveis.
