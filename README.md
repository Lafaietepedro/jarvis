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
- Auditoria local da memória com filtros
- Exclusão seletiva da memória local com confirmação
- Painel de privacidade e permissões
- CLI local para painel, histórico e comandos
- Diagnóstico local de dependências opcionais
- Validação e plano de instalação de dependências opcionais
- Chat interativo no terminal
- Interface web local em `GET /ui`
- Auditoria de memória visível na interface web local
- Filtros de auditoria de memória na interface web local
- Manifest local e gerador de atalho desktop
- Skill inicial de navegador/pesquisa
- Skill inicial de IDE/projeto
- Snapshot local de projeto para comandos, arquivos e marcadores
- Sugestões proativas baseadas em histórico local e snapshot do projeto
- Planos seguros de automação
- Executor de automações com checkpoints
- Confirmação de checkpoints pendentes
- Painel CLI de checkpoints pendentes
- Confirmação rápida de checkpoints pelo CLI/chat
- Histórico curto de eventos de checkpoints na sessão
- Endpoint dedicado para checkpoints e eventos
- Resumo de checkpoints com severidade, mensagens e próximos passos
- Contrato agregado para UI desktop em `GET /ui/state`
- Preview CLI do contrato de UI desktop
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
python -m app.cli checkpoints
python -m app.cli ui-state
python -m app.cli desktop-launcher
python -m app.cli desktop-launcher --output ../jarvis.desktop
python -m app.cli install-desktop-launcher
python -m app.cli confirm-checkpoint 1
python -m app.cli watch
python -m app.cli presence
python -m app.cli privacy
python -m app.cli diagnostics
python -m app.cli dependencies
python -m app.cli install-dependencies
python -m app.cli history
python -m app.cli memory-audit
python -m app.cli memory-audit --intent status
python -m app.cli memory-delete --id 1 --confirm
python -m app.cli memory-delete --intent status --confirm
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
- `GET /ui` — interface web local do JARVIS
- `GET /presence` — estado detalhado de presença, privacidade e contexto
- `GET /health` — healthcheck
- `POST /start` — inicia loop de wake+listen (simulado wake) e fala uma saudação
- `POST /stop` — para loop
- `POST /pause` — pausa a presença operacional do JARVIS
- `POST /resume` — retorna ao estado ativo
- `POST /command` — executa um comando em texto e retorna intent/ação/resposta/sugestões/contexto
- `GET /context` — mostra o contexto local usado pelo JARVIS
- `GET /history` — lista comandos recentes registrados localmente
- `GET /history/audit` — resume a memória local com filtros por intenção, skill, ação e data
- `GET /history/export` — exporta histórico local como JSON
- `POST /history/delete` — remove memórias por id ou filtro com confirmação
- `POST /history/clear` — limpa histórico local com confirmação
- `GET /checkpoints` — lista checkpoints pendentes e eventos recentes
- `GET /ui/state` — agrega presença, checkpoints, histórico curto e privacidade para UI desktop
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
- `resumo da memoria`
- `apagar comando 1`
- `exportar historico`
- `limpar historico`
- `painel de privacidade`
- `diagnostico`
- `validar dependencias opcionais`
- `instalar dependencias opcionais`
- `checkpoints pendentes`
- `pesquisar por python fastapi`
- `abrir site example.com`
- `comandos do projeto`
- `estado do projeto`
- `abrir projeto`
- `checkup do projeto`
- `rotina de desenvolvimento`
- `executar checkup do projeto`
- `executar rotina de desenvolvimento`
- `confirmar checkpoint 1`
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

Automações com checkpoints
- `checkup do projeto` e `rotina de desenvolvimento` apenas montam planos revisáveis.
- `executar checkup do projeto` e `executar rotina de desenvolvimento` executam somente passos seguros de leitura, como diagnóstico, comandos detectados e painel de privacidade.
- Passos com risco médio, abertura de apps, comandos de shell ou permissões explícitas viram checkpoints e não são executados automaticamente.
- Depois de revisar, use `confirmar checkpoint 1` para confirmar um checkpoint pendente. Mesmo confirmado, o passo ainda respeita as permissões do sistema, como `JARVIS_ENABLE_SHELL` e `JARVIS_ENABLE_IDE_ACTIONS`.

Permissões
- Ações de desktop ficam bloqueadas por padrão. Para permitir abertura real de apps:

```bash
export JARVIS_ENABLE_DESKTOP_ACTIONS=1
```

- Ações de navegador ficam bloqueadas por padrão. Para permitir abertura de URL/pesquisa:

```bash
export JARVIS_ENABLE_BROWSER_ACTIONS=1
```

- Ações de IDE ficam bloqueadas por padrão. Para permitir abrir o projeto no VS Code:

```bash
export JARVIS_ENABLE_IDE_ACTIONS=1
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

Checkpoints pendentes:

```bash
curl http://localhost:8000/checkpoints
make checkpoints
make confirm-checkpoint ID=1
```

O painel de checkpoints também mostra eventos recentes da sessão, como confirmações bloqueadas por permissão ou execuções concluídas.
Os relatórios incluem severidade, mensagem legível e próximo passo sugerido.

Contrato para UI desktop:

```bash
curl http://localhost:8000/ui/state
make ui-state
```

Esse endpoint reúne presença, checkpoints, histórico curto, privacidade, capacidades do projeto, próximas ações e metadados de risco/permissão em um payload estável para interfaces locais.

Interface local:

```text
http://localhost:8000/ui
```

A interface usa apenas assets locais servidos pelo backend, mostra eventos recentes de checkpoints e permite configurar o refresh automatico.

Atalho desktop:

```bash
make desktop-launcher
make install-desktop-launcher
cd backend
python -m app.cli desktop-launcher --output ../jarvis.desktop
python -m app.cli install-desktop-launcher --confirm
```

O comando `desktop-launcher` apenas gera um arquivo `.desktop`. O comando `install-desktop-launcher` exige `--confirm` antes de escrever em `~/.local/share/applications`.

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
/?
/panel
/p
/ui-state
/ui
/checkpoints
/chk
/confirm-checkpoint 1
/cc 1
/privacy
/priv
/diagnostics
/diag
/dependencies
/deps
/install-dependencies
/install-deps
/history
/hist
/memory-audit
/mem
/memory-delete
/session
/s
/export-history
/clear-history
/private qual o status
/pv qual o status
/confirm rode make test
/c rode make test
/speak qual o status
/say qual o status
/exit
/q
```

Diagnóstico local:

```bash
curl http://localhost:8000/diagnostics
python -m app.cli diagnostics
make dependencies
make install-dependencies
```

Testes

```bash
make test
```

Para validar tambem os contratos reais da API quando a `.venv` estiver instalada:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests
```

Para rodar apenas o smoke HTTP local, quando sockets localhost estiverem disponiveis:

```bash
cd backend
.venv/bin/python -m unittest tests/test_api_smoke.py -v
```

Esse smoke cobre healthcheck, presenca, pausa/retomada, comando, historico e eventos de checkpoints via servidor local real.

Para validar a interface em Chromium headless, quando disponivel:

```bash
cd backend
.venv/bin/python -m unittest tests/test_ui_browser_smoke.py -v
```

Esse smoke confere conteudo renderizado e screenshots desktop/mobile.

Em um Python sem FastAPI instalada, os testes de contrato da API sao pulados automaticamente. Em ambientes que bloqueiam sockets localhost, os smokes HTTP e visual tambem sao pulados.

Notas
- Este PoC usa um simulador de wake-word por simplicidade. Substitua por Porcupine/Precise quando estiver pronto.
- Baixe modelos Vosk apropriados e defina `VOSK_MODEL_PATH`.
- Home Assistant fica como skill futura/opcional. O foco atual é o assistente local do computador.

Roadmap curto
- Expandir skills locais: automações executáveis com confirmação e integrações de IDE mais profundas.
- Evoluir a skill de IDE com leitura autorizada de estado do editor no futuro.
- Evoluir a skill de navegador com leitura autorizada de abas/bookmarks no futuro.
- Evoluir memória local e painel de privacidade.
- Evoluir a interface CLI para comandos interativos mais ricos.
- Melhorar voz 24/7 com wake-word e VAD local.
- Adicionar companion mobile para comandos, notificações e confirmação de ações.
- Reintroduzir casa conectada via Home Assistant/MQTT como skill opcional.
