# J.A.R.V.I.S. Development Log

Este documento acompanha o estado do desenvolvimento do J.A.R.V.I.S. Ele deve ser atualizado a cada avanço relevante para manter claro o que ja foi entregue, o que esta em desenvolvimento ativo e o que esta planejado.

## Estado Atual

O projeto esta na fase de fundacao do assistente local-first. O foco atual deixou de ser automacao residencial e passou a ser um assistente privado para controlar o computador por comandos de texto e, depois, voz.

O nucleo atual ja consegue:
- receber comandos por `POST /command`;
- indicar presenca ativa por `GET /` e `GET /presence`;
- saudar o usuario ao iniciar o modo voz por `POST /start`;
- alternar estado de sessao por `POST /pause` e `POST /resume`;
- registrar historico local em SQLite, com modo privado por comando;
- interpretar intencoes simples com NLU rule-based;
- rotear intencoes para skills locais;
- consultar politica central de permissoes antes de acoes sensiveis;
- exibir painel de privacidade por `GET /privacy` ou comando em linguagem natural;
- coletar contexto local do projeto;
- analisar capacidades de projeto com uma skill dev inicial;
- consultar status de midia/audio e preparar controles de volume/reproducao;
- preparar abertura de URL e pesquisa web com permissao explicita;
- listar comandos de projeto e preparar abertura do workspace na IDE;
- montar planos seguros de automacao com revisao manual obrigatoria;
- executar automacoes seguras de leitura com checkpoints para qualquer passo sensivel;
- lembrar checkpoints pendentes na sessao e aceitar confirmacao por comando natural;
- listar checkpoints pendentes por comando natural, CLI, chat e painel local;
- exibir um painel CLI local por `python -m app.cli panel` ou `make panel`;
- exibir diagnostico local por `GET /diagnostics`, comando natural ou `python -m app.cli diagnostics`;
- atualizar painel vivo por `python -m app.cli watch`;
- conversar pelo terminal com `python -m app.cli chat` ou `make chat`;
- exportar e limpar historico local por API, CLI ou comando natural confirmado;
- retornar sugestoes de proximas acoes;
- expor `GET /context` para auditar o contexto usado;
- expor `GET /history` para consultar comandos recentes;
- manter acoes sensiveis bloqueadas por padrao;
- executar testes automatizados do core e do NLU.

## Fases Completadas

### Fase 0 - PoC Inicial Offline-First

Status: concluida.

Entregas:
- API FastAPI inicial.
- Healthcheck em `GET /health`.
- Fluxo basico de wake/listen com wake-word simulado.
- ASR local via Vosk, dependente de `VOSK_MODEL_PATH`.
- TTS via `pyttsx3` com fallback para `espeak`.
- Endpoint `POST /recognize_file` para transcrever WAV.
- Integracao inicial com Home Assistant como prova de conceito.

Observacao:
- Home Assistant foi rebaixado para integracao futura/opcional. O foco principal agora e controle local do computador.

### Fase 1 - Comando Por Texto E NLU Melhorado

Status: concluida.

Entregas:
- Endpoint `POST /command`.
- Executor de comando reutilizavel pelo fluxo de voz.
- NLU com normalizacao de acentos.
- Deteccao de comandos como status, ligar/desligar luz e ambientes.
- Testes unitarios iniciais do NLU.
- Correcao para evitar confundir `desligar` com `ligar`.

### Fase 2 - Nucleo Local-First E Skills

Status: concluida.

Entregas:
- `JarvisCore` como orquestrador central.
- Sistema inicial de skills em `backend/app/skills/`.
- `SystemSkill` para status e capacidades.
- `FileSkill` para listar arquivos e informar diretorio atual.
- `ComputerSkill` para preparar abertura de apps conhecidos.
- `ShellSkill` para preparar comandos de shell com confirmacao.
- `LocalContextProvider` para detectar projeto, marcadores e flags de privacidade.
- Motor simples de sugestoes contextuais.
- Endpoint `GET /context`.
- Resposta do `/command` expandida com `intent`, `action`, `suggestions`, `context` e `data`.
- Politica conservadora: desktop actions e shell desativados por padrao.
- Testes automatizados do core.

### Fase 3A - Sessao, Permissoes E Memoria Local

Status: concluida.

Entregas:
- `SessionState` central para estados `active`, `listening`, `processing` e `paused`.
- Endpoints `POST /pause` e `POST /resume`.
- `PermissionPolicy` centralizada para shell e acoes de desktop.
- `MemoryStore` local em SQLite.
- Historico local por `GET /history`.
- Flag `private` no `POST /command` para nao registrar comandos sensiveis.
- `.jarvis/` ignorado pelo Git para guardar estado local.
- `MemorySkill` para consultar ultimos comandos por linguagem natural.
- `DevSkill` para analisar projeto, preparar ambiente e sugerir testes.
- NLU expandido para `analisar projeto`, `rodar testes`, `ultimos comandos` e comandos de preparacao.
- Testes de memoria, permissoes, sessao e dev/core.

### Fase 3B - Privacidade Auditavel E Midia Inicial

Status: concluida.

Entregas:
- `PrivacySkill` com painel textual de privacidade, memoria, sessao e permissoes.
- Endpoint `GET /privacy`.
- Estatisticas de memoria local em `MemoryStore`.
- Flag `media_actions_enabled` no contexto local.
- `MediaSkill` para status de audio/player e acoes de volume/reproducao.
- Politica `JARVIS_ENABLE_MEDIA_ACTIONS` para bloquear mudancas de midia por padrao.
- NLU expandido para `painel de privacidade`, `status do audio`, `aumentar volume`, `diminuir volume`, `pausar musica` e comandos relacionados.
- Testes para painel de privacidade, permissoes de midia e intents de midia.

### Fase 3C - CLI Local De Operacao

Status: concluida.

Entregas:
- Modulo `app.cli` para operar o J.A.R.V.I.S. via terminal.
- Comandos CLI: `panel`, `presence`, `privacy`, `history`, `ask`, `pause`, `resume`, `start` e `stop`.
- Formatadores testaveis em `app.cli_format`.
- Target `make panel`.
- Target `make ask TEXT="..."`.
- Suporte a `JARVIS_URL` para apontar o CLI para outra instancia local.
- Testes dos formatadores do painel.

### Fase 3D - Painel Vivo E Diagnostico Local

Status: concluida.

Entregas:
- Modulo `diagnostics` para mapear sistema, Python, Vosk e binarios opcionais.
- Endpoint `GET /diagnostics`.
- Intent `diagnostics` para comandos como `diagnostico` e `saude do sistema`.
- `SystemSkill` respondendo diagnostico local.
- CLI `diagnostics`.
- CLI `watch` para atualizar o painel em tempo real.
- O painel CLI agora inclui diagnostico local.
- Testes de NLU, core, formatadores e watch.

### Fase 3E - Chat Interativo No CLI

Status: concluida.

Entregas:
- CLI `chat` para conversar em loop pelo terminal.
- Target `make chat`.
- Comandos locais no chat: `/help`, `/panel`, `/presence`, `/privacy`, `/diagnostics`, `/history`, `/pause`, `/resume`, `/start`, `/stop` e `/exit`.
- Prefixos de envio: `/private`, `/confirm` e `/speak`.
- Testes para parsing de linhas, ações do chat e encerramento do loop.

### Fase 3F - Gestao Auditavel Do Historico

Status: concluida.

Entregas:
- `MemoryStore.export_history` para gerar exportacao JSON do historico local.
- `MemoryStore.clear_history` retornando a quantidade de comandos removidos.
- Endpoint `GET /history/export`.
- Endpoint `POST /history/clear` com confirmacao obrigatoria.
- `MemorySkill` com intents `export_history` e `clear_history`.
- NLU expandido para `exportar historico` e `limpar historico`.
- CLI `export-history`, com suporte a `--output`.
- CLI `clear-history --confirm`.
- Comandos de chat `/export-history` e `/clear-history`.
- Testes para exportacao, limpeza, intents, core, formatadores e CLI.

### Fase 3G - Navegador Seguro Inicial

Status: concluida.

Entregas:
- `BrowserSkill` para abrir URL e preparar pesquisas web.
- Normalizacao segura de URL com suporte apenas a HTTP/HTTPS.
- Politica `JARVIS_ENABLE_BROWSER_ACTIONS` para bloquear abertura de navegador por padrao.
- Flag `browser_actions_enabled` no contexto local e painel de privacidade.
- NLU expandido para `pesquisar por ...` e `abrir site ...`.
- Sugestoes contextuais incluindo pesquisa de documentacao.
- Testes para permissoes, NLU, core e normalizacao de URL.

### Fase 3H - IDE E Comandos De Projeto

Status: concluida.

Entregas:
- `IDESkill` para listar comandos detectados no projeto.
- Deteccao de targets do `Makefile`.
- Deteccao de scripts do `package.json`.
- Sugestao de `docker compose up` quando `docker-compose.yml` existe.
- Preparacao para abrir workspace no VS Code.
- Politica `JARVIS_ENABLE_IDE_ACTIONS` para bloquear abertura da IDE por padrao.
- Flag `ide_actions_enabled` no contexto local e painel de privacidade.
- NLU expandido para `comandos do projeto` e `abrir projeto`.
- Testes para permissoes, NLU, core, formatadores e deteccao de comandos.

### Fase 3I - Planos Seguros De Automacao

Status: concluida.

Entregas:
- `AutomationSkill` para montar planos sem executar ações sensiveis.
- Plano `project_checkup` com diagnostico, comandos do projeto, testes confirmaveis e privacidade.
- Plano `development_routine` com abertura de IDE, comandos detectados e opções de desenvolvimento.
- Campo `execution=manual_review_required` para deixar claro que a rotina não executa sozinha.
- NLU expandido para `checkup do projeto` e `rotina de desenvolvimento`.
- Testes para montagem de planos, NLU e roteamento pelo core.

### Fase 3J - Executor De Automacoes Com Checkpoints

Status: concluida.

Entregas:
- Execucao de planos por `executar checkup do projeto` e `executar rotina de desenvolvimento`.
- Execucao automatica apenas de passos seguros e de leitura.
- Checkpoints obrigatorios para comandos de shell, abertura de IDE, permissoes explicitas ou passos de risco medio.
- Relatorio estruturado com `executed_steps`, `checkpoints` e `results`.
- Resumo de privacidade executavel como passo seguro, sem sair do dispositivo.
- Fechamento explicito das conexoes SQLite usadas pela memoria local.
- Testes de NLU, core, executor de automacao e memoria por comportamento existente.

### Fase 3K - Confirmacao De Checkpoints Pendentes

Status: concluida.

Entregas:
- Sessao agora guarda checkpoints de automacao pendentes.
- Snapshot de sessao expõe checkpoints com `checkpoint_id`, plano, label e motivo.
- NLU expandido para comandos como `confirmar checkpoint 1`, `aprovar passo 2` e `executar checkpoint 1`.
- `AutomationSkill` confirma checkpoints pendentes e delega para skills existentes.
- Checkpoints de shell passam por `ShellSkill` com confirmacao explicita, mas continuam bloqueados se `JARVIS_ENABLE_SHELL` nao estiver ativo.
- Checkpoints de IDE passam por `IDESkill` e respeitam `JARVIS_ENABLE_IDE_ACTIONS`.
- Checkpoints bloqueados permanecem pendentes para nova tentativa depois de ajustar permissoes.
- Testes cobrindo sessao, NLU, core e delegacao de checkpoint.

### Fase 3L - Visibilidade De Checkpoints No CLI

Status: concluida.

Entregas:
- `GET /presence` agora inclui `automation_checkpoints`.
- Painel CLI mostra contagem de checkpoints pendentes.
- Novo formatador `[CHECKPOINTS]` para listar checkpoint, plano, motivo e comando de confirmacao.
- Novo comando `python -m app.cli checkpoints`.
- Novo target `make checkpoints`.
- Chat interativo ganhou `/checkpoints`.
- NLU expandido para `checkpoints pendentes`, `listar checkpoints` e termos relacionados.
- `AutomationSkill` responde `pending_checkpoints` com sugestoes de confirmacao.
- Testes cobrindo presença, CLI, formatadores, NLU e core.

## Em Desenvolvimento Ativo

### Fase 3 - Assistente Local Do Computador

Status: em desenvolvimento ativo.

Objetivo:
- Tornar o J.A.R.V.I.S. util no computador antes de expandir para celular e casa.

Prioridades atuais:
- Expandir o NLU para mais comandos locais.
- Criar confirmacao de checkpoints mais ergonomica no chat/CLI.
- Evoluir integracoes de IDE mais profundas.
- Evoluir a presenca para um indicador visual persistente de estado ativo/ouvindo/pausado.
- Melhorar a politica de permissoes por risco e por tipo de alvo.
- Melhorar sugestoes com base em historico recente.
- Tornar a memoria local mais auditavel e editavel.

Primeiras tarefas recomendadas:
- Adicionar testes de contrato para `/command` e `/context`.
- Adicionar testes de contrato para `/presence`, `/history`, `/pause` e `/resume`.
- Melhorar o chat com histórico de sessão e comandos abreviados.
- Criar comandos para instalar/validar dependencias opcionais.
- Criar comando CLI dedicado para confirmar checkpoint por id.

## Fases Futuras Planejadas

### Fase 4 - Voz Local 24/7 Com Privacidade

Status: planejada.

Objetivo:
- Ativar experiencia de voz continua sem comprometer privacidade.

Planejado:
- Wake-word local real.
- VAD local para detectar fala.
- Ring buffer em memoria, sem persistir audio por padrao.
- Comandos de privacidade: `pare de ouvir`, `modo privado`, `esqueca isso`.
- Indicador claro de estado: ouvindo, processando, pausado.
- Testes de fluxo sem depender de microfone real.

### Fase 5 - Proatividade E Memoria

Status: planejada.

Objetivo:
- Transformar sugestoes simples em comportamento contextual mais inteligente.

Planejado:
- Memoria local de preferencias.
- Historico recente de comandos e resultados.
- Sugestoes baseadas em padroes do usuario.
- Painel "o que o J.A.R.V.I.S. sabe sobre mim".
- Modo privado sem gravar memoria.
- Explicacao de por que uma sugestao foi feita.

### Fase 6 - Interface Desktop

Status: planejada.

Objetivo:
- Tirar o assistente do `curl` e criar uma experiencia de uso real.

Planejado:
- Overlay local tipo command palette.
- Atalho global.
- Tray indicator.
- Indicador visual de presenca do J.A.R.V.I.S.
- Historico de comandos.
- Confirmacoes visuais para acoes sensiveis.
- Painel de privacidade e permissoes.

### Fase 7 - Companion Mobile

Status: planejada.

Objetivo:
- Expandir o J.A.R.V.I.S. para celular sem duplicar o core.

Planejado:
- App companion Android primeiro.
- Celular como microfone remoto.
- Notificacoes e confirmacoes de acoes.
- Comandos remotos para o core no computador.
- Autenticacao local segura.
- iOS via app/Shortcuts quando fizer sentido.

### Fase 8 - Casa Conectada

Status: planejada.

Objetivo:
- Reintroduzir automacao residencial como skill opcional.

Planejado:
- Skill Home Assistant.
- Skill MQTT.
- Rotinas de casa.
- Permissoes por dispositivo/ambiente.
- Suporte futuro a Matter/Zigbee/Z-Wave via hubs existentes.

### Fase 9 - LLM Local E Agentes Especializados

Status: planejada.

Objetivo:
- Evoluir de regras simples para raciocinio local/hibrido com controle de privacidade.

Planejado:
- Classificacao de intencao com modelo local.
- Planejamento multi-step com confirmacoes.
- Agentes especializados: dev, navegador, arquivos, agenda e automacao.
- Modo hibrido opcional com nuvem apenas quando autorizado.

## Decisoes De Produto

- Privacidade e requisito central, nao opcional.
- O core deve chamar skills; ele nao deve virar uma classe gigante que controla tudo.
- Sugestoes podem ser proativas, mas execucoes sensiveis devem exigir confirmacao.
- Acoes destrutivas devem ser bloqueadas ate existir politica de permissao robusta.
- Celular e casa sao expansoes; o primeiro produto utilizavel deve ser o assistente local do computador.

## Verificacao Atual

Ultima verificacao registrada:

```bash
make test
```

Resultado esperado no estado atual:

```text
104 tests OK
```

```bash
python -m compileall backend/app
```

Resultado esperado:

```text
sem erros de compilacao
```
