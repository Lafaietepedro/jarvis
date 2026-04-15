# J.A.R.V.I.S. — Assistente local-first

Projeto inicial para um assistente multimodal estilo J.A.R.V.I.S. com foco em controle local do computador, privacidade por padrão e expansão futura para celular e casa conectada.

Status do desenvolvimento: veja o log em [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md).

Visão rápida
- Controle por texto via API local
- Presença ativa via `GET /` e `GET /presence`
- Estado de sessão: ativo, ouvindo, processando e pausado
- Núcleo de skills expansível
- Contexto local do projeto/computador
- Memória local de histórico em SQLite
- Painel de privacidade e permissões
- CLI local para painel, histórico e comandos
- Diagnóstico local de dependências opcionais
- Chat interativo no terminal
- Skill inicial de mídia/volume
- Sugestões de próximas ações
- Permissões conservadoras para ações sensíveis
- Wake-word (simulado)
- ASR: Vosk (local)
- NLU: rule-based simples, com caminho para LLM local
- TTS: pyttsx3 / espeak fallback

Princípios
- Local-first: áudio, contexto e memória devem ficar no dispositivo por padrão.
- Privacidade inegociável: nada de nuvem sem configuração explícita.
- Skills antes de integrações gigantes: o core roteia intenções para capacidades isoladas.
- Sugestão não é execução: ações sensíveis pedem confirmação.
- Casa e celular entram como expansões, não como dependência do núcleo.

Pré-requisitos (desenvolvimento)
- Python 3.11+
- Linux (Intel NUC recomendado) com audio input/output configurado
- Vosk model opcional para voz (baixe e extraia, defina `VOSK_MODEL_PATH`)

Como rodar localmente (rápido)

```bash
# Entrar na pasta backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Opcional: defina o caminho do modelo Vosk (baixe um modelo 16kHz)
export VOSK_MODEL_PATH=/caminho/para/model

# Rodar em desenvolvimento
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

CLI local

Com o backend rodando, use:

```bash
make panel
```

Ou diretamente:

```bash
cd backend
python -m app.cli panel
python -m app.cli watch
python -m app.cli presence
python -m app.cli privacy
python -m app.cli diagnostics
python -m app.cli history
python -m app.cli export-history
python -m app.cli export-history --output history.json
python -m app.cli clear-history --confirm
python -m app.cli ask "qual o status"
python -m app.cli ask "rode make test" --confirm
python -m app.cli chat
python -m app.cli pause
python -m app.cli resume
```

Também é possível apontar para outra URL:

```bash
JARVIS_URL=http://127.0.0.1:8000 python -m app.cli panel
```

Endpoints úteis
- `GET /` — saudação e estado de presença do JARVIS
- `GET /presence` — estado detalhado de presença, privacidade e contexto
- `GET /health` — healthcheck
- `POST /start` — inicia loop de wake+listen (simulado wake) e fala uma saudação
- `POST /stop` — para loop
- `POST /pause` — pausa a presença operacional do JARVIS
- `POST /resume` — retorna ao estado ativo
- `POST /command` — executa um comando em texto e retorna intent/ação/resposta/sugestões/contexto
- `GET /context` — mostra o contexto local usado pelo JARVIS
- `GET /history` — lista comandos recentes registrados localmente
- `GET /history/export` — exporta histórico local como JSON
- `POST /history/clear` — limpa histórico local com confirmação
- `GET /privacy` — mostra painel de privacidade, memória, sessão e permissões
- `GET /diagnostics` — mostra dependências opcionais e saúde local
- `POST /recognize_file` — faz upload de WAV e retorna transcrição

Exemplo de comando em texto

```bash
curl http://localhost:8000/presence
```

```bash
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text":"qual o status"}'
```

Comandos iniciais
- `qual o status`
- `listar arquivos`
- `onde estou`
- `abrir terminal`
- `rode make test`
- `analisar projeto`
- `rodar testes`
- `ultimos comandos`
- `exportar historico`
- `limpar historico`
- `painel de privacidade`
- `diagnostico`
- `status do audio`
- `aumentar volume`
- `diminuir volume`
- `pausar musica`
- `o que voce pode controlar neste computador`

Presença e sessão

```bash
curl http://localhost:8000/presence
curl -X POST http://localhost:8000/pause
curl -X POST http://localhost:8000/resume
```

Histórico local
- O histórico de comandos fica em SQLite, por padrão em `.jarvis/memory.sqlite` dentro do workspace.
- `.jarvis/` é ignorado pelo Git.
- Para exportar o histórico:

```bash
cd backend
python -m app.cli export-history --output history.json
```

- Para limpar o histórico:

```bash
cd backend
python -m app.cli clear-history --confirm
```

- Para desativar memória:

```bash
export JARVIS_DISABLE_MEMORY=1
```

- Para executar um comando sem registrar no histórico:

```bash
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text":"qual o status","private":true}'
```

Permissões
- Ações de desktop ficam bloqueadas por padrão. Para permitir abertura real de apps:

```bash
export JARVIS_ENABLE_DESKTOP_ACTIONS=1
```

- Comandos de shell exigem `confirm_actions=true` no request e ainda ficam bloqueados por padrão. Para permitir execução real:

```bash
export JARVIS_ENABLE_SHELL=1
```

- Ações de mídia/volume também ficam bloqueadas por padrão. Para permitir:

```bash
export JARVIS_ENABLE_MEDIA_ACTIONS=1
```

Exemplo com confirmação:

```bash
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text":"rode make test","confirm_actions":true}'
```

Painel de privacidade:

```bash
curl http://localhost:8000/privacy
```

Ou pelo CLI:

```bash
make panel
```

Painel vivo:

```bash
cd backend
python -m app.cli watch
```

Chat interativo:

```bash
make chat
```

Dentro do chat:

```text
/help
/panel
/privacy
/diagnostics
/history
/export-history
/clear-history
/private qual o status
/confirm rode make test
/speak qual o status
/exit
```

Diagnóstico local:

```bash
curl http://localhost:8000/diagnostics
python -m app.cli diagnostics
```

Testes

```bash
make test
```

Notas
- Este PoC usa um simulador de wake-word por simplicidade. Substitua por Porcupine/Precise quando estiver pronto.
- Baixe modelos Vosk apropriados e defina `VOSK_MODEL_PATH`.
- Home Assistant fica como skill futura/opcional. O foco atual é o assistente local do computador.

Roadmap curto
- Expandir skills locais: navegador, IDE e automações.
- Evoluir memória local e painel de privacidade.
- Evoluir a interface CLI para comandos interativos mais ricos.
- Melhorar voz 24/7 com wake-word e VAD local.
- Adicionar companion mobile para comandos, notificações e confirmação de ações.
- Reintroduzir casa conectada via Home Assistant/MQTT como skill opcional.
