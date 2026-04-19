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
- auditar memoria local com filtros por intent, skill, acao e data;
- apagar entradas especificas da memoria local por id ou filtro confirmado;
- interpretar intencoes simples com NLU rule-based;
- interpretar pedidos compostos com multiplas acoes em uma mesma frase;
- rotear intencoes para skills locais;
- consultar politica central de permissoes antes de acoes sensiveis;
- exibir painel de privacidade por `GET /privacy` ou comando em linguagem natural;
- coletar contexto local do projeto;
- localizar arquivos por nome dentro do workspace;
- ler e resumir arquivos de texto do workspace com limite de tamanho;
- preparar propostas de edicao de arquivo com diff, sem gravar no disco;
- aplicar propostas de edicao apenas por checkpoint confirmado;
- analisar capacidades de projeto com uma skill dev inicial;
- consultar status de midia/audio e preparar controles de volume/reproducao;
- preparar abertura de URL e pesquisa web com permissao explicita;
- listar comandos de projeto e preparar abertura do workspace na IDE;
- gerar snapshot local de projeto com comandos, arquivos e marcadores;
- sugerir proximos passos com base em historico local recente e snapshot do projeto;
- classificar risco de acoes por tipo, alvo, permissao e necessidade de confirmacao;
- montar planos seguros de automacao com revisao manual obrigatoria;
- executar automacoes seguras de leitura com checkpoints para qualquer passo sensivel;
- criar checkpoints dedicados para etapas sensiveis dentro de pedidos compostos;
- lembrar checkpoints pendentes na sessao e aceitar confirmacao por comando natural;
- listar checkpoints pendentes por comando natural, CLI, chat e painel local;
- confirmar checkpoints por id no CLI e no chat;
- revisar checkpoints no CLI com origem, etapa, risco, comando e proximos passos;
- registrar eventos recentes de checkpoints confirmados na sessao;
- expor checkpoints e eventos por endpoint dedicado `GET /checkpoints`;
- resumir checkpoints com severidade, mensagens e proximos passos;
- detalhar checkpoints por origem e etapa pendente, inclusive comandos compostos;
- auditar eventos de checkpoints com origem, etapa, comando e resultado delegado;
- expor estado agregado para UI desktop por `GET /ui/state`;
- expor capacidades do projeto e permissoes operacionais no contrato de UI;
- visualizar o contrato de UI desktop por CLI e chat;
- servir uma interface web local por `GET /ui`;
- controlar comandos, pausa/retomada e checkpoints pela interface web local;
- preparar manifest local e atalho desktop sem instalacao automatica;
- exibir um painel CLI local por `python -m app.cli panel` ou `make panel`;
- exibir diagnostico local por `GET /diagnostics`, comando natural ou `python -m app.cli diagnostics`;
- validar dependencias opcionais por comando natural, CLI ou chat;
- preparar comandos de instalacao de dependencias opcionais sem executar instalacao automaticamente;
- validar a API por smoke test HTTP local quando sockets localhost estao disponiveis;
- atualizar painel vivo por `python -m app.cli watch`;
- conversar pelo terminal com `python -m app.cli chat` ou `make chat`;
- usar atalhos e historico curto de sessao no chat interativo;
- exportar e limpar historico local por API, CLI ou comando natural confirmado;
- retornar sugestoes de proximas acoes;
- expor `GET /context` para auditar o contexto usado;
- expor `GET /history` para consultar comandos recentes;
- expor `GET /history/audit` para resumir a memoria local com filtros;
- expor `POST /history/delete` para exclusao seletiva da memoria local;
- exibir auditoria da memoria local no contrato de UI e na interface web;
- filtrar auditoria da memoria local pela interface web;
- apagar memorias locais pela interface web com confirmacao;
- cobrir contratos da API para presenca, checkpoints, contexto, historico e sessao;
- cobrir contrato agregado para futuras interfaces locais;
- manter acoes sensiveis bloqueadas por padrao;
- validar por HTTP real os estados de pausa/retomada e eventos de checkpoints;
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

### Fase 3M - Confirmacao Ergonomica De Checkpoints

Status: concluida.

Entregas:
- Novo comando `python -m app.cli confirm-checkpoint <id>`.
- Novo target `make confirm-checkpoint ID=<id>`.
- Chat interativo ganhou `/confirm-checkpoint <id>`.
- Parser do chat valida ids invalidos e orienta o formato correto.
- Confirmacao rapida continua passando por `POST /command` com `confirmar checkpoint <id>`.
- Confirmacao rapida preserva o caminho seguro de `AutomationSkill`, `ShellSkill`, `IDESkill` e permissoes existentes.
- Testes cobrindo parser do chat, acao de chat e comando CLI.

### Fase 3N - Feedback E Historico Curto De Checkpoints

Status: concluida.

Entregas:
- `SessionState` agora registra eventos recentes de checkpoints confirmados.
- Eventos guardam checkpoint, plano, label, status, motivo, skill delegada e resposta.
- Historico de eventos fica limitado aos 10 registros mais recentes na sessao.
- `GET /presence` agora inclui `automation_checkpoint_events`.
- Painel CLI mostra a quantidade de eventos recentes.
- Seção `[CHECKPOINTS]` mostra eventos recentes junto com pendencias atuais.
- Comando natural `checkpoints pendentes` retorna pendencias e eventos recentes.
- Testes cobrindo sessao, automacao, core, presença e formatadores CLI.

### Fase 3O - Endpoint Dedicado De Checkpoints

Status: concluida.

Entregas:
- Novo modulo `checkpoints` para montar estado de checkpoints e eventos.
- Endpoint `GET /checkpoints` com `status`, `pending_count`, `event_count`, `checkpoints` e `events`.
- CLI `checkpoints`, painel e chat agora leem o endpoint dedicado.
- `format_checkpoints` aceita tanto o payload dedicado quanto o payload legado de presença.
- Painel CLI recebe o payload dedicado de checkpoints quando disponivel.
- Testes cobrindo estado dedicado, formatador, painel e uso do endpoint pelo CLI/chat.

### Fase 3P - Testes De Contrato Da API

Status: concluida.

Entregas:
- Testes de contrato para `GET /presence`.
- Testes de contrato para `GET /checkpoints`.
- Testes de contrato para `POST /command` criando checkpoints e eventos.
- Isolamento do `JarvisCore` global durante os testes de contrato.
- Testes de contrato pulam automaticamente quando dependencias web nao estao instaladas no Python em uso.
- Validacao completa na `.venv` roda os contratos reais com FastAPI disponivel.

### Fase 3Q - Contratos De Contexto, Historico E Sessao

Status: concluida.

Entregas:
- Teste de contrato para `GET /context` validando projeto, marcadores, capacidades e flags de privacidade.
- Teste de contrato para `GET /history` validando o formato dos comandos recentes registrados localmente.
- Teste de contrato para `POST /pause` validando transicao para sessao pausada e voz desligada.
- Teste de contrato para `POST /resume` validando retorno para sessao ativa.
- Isolamento do estado global de voz nos testes de contrato.

### Fase 3R - Chat Com Atalhos E Historico De Sessao

Status: concluida.

Entregas:
- Atalhos no chat para comandos frequentes, como `/p`, `/chk`, `/cc <id>`, `/hist`, `/priv` e `/diag`.
- Atalhos para envio com opcoes, como `/pv <texto>`, `/c <texto>` e `/say <texto>`.
- Novo comando `/session` com alias `/s` para mostrar o historico curto da sessao atual do chat.
- Historico de sessao mantido apenas em memoria pelo `chat_loop`, separado do historico persistente em SQLite.
- Ajuda do chat atualizada com os atalhos disponiveis.
- Testes cobrindo parsing dos atalhos, historico de sessao e loop interativo.

### Fase 3S - Validacao De Dependencias Opcionais

Status: concluida.

Entregas:
- Diagnostico agora inclui modulos Python opcionais usados por voz local, como `vosk`, `sounddevice`, `soundfile` e `pyttsx3`.
- Novo relatorio estruturado de dependencias opcionais, com binarios ausentes, modulos Python ausentes, modelo Vosk e comandos sugeridos.
- Novo comando natural `validar dependencias opcionais`.
- Novo comando natural `instalar dependencias opcionais`, que prepara comandos e nao executa instalacao automaticamente.
- Novos comandos CLI `dependencies` e `install-dependencies`.
- Novos targets `make dependencies` e `make install-dependencies`.
- Chat interativo ganhou `/dependencies`, `/deps`, `/install-dependencies` e `/install-deps`.
- Diagnostico CLI agora mostra contagem e ausencias de modulos Python opcionais.
- Testes cobrindo NLU, core, CLI e relatorio de dependencias opcionais.

### Fase 3T - Smoke Test HTTP Local

Status: concluida.

Entregas:
- Novo smoke test HTTP com `uvicorn` e `urllib`, sem depender de `httpx`/`TestClient`.
- O teste sobe a API em `127.0.0.1` usando porta local livre.
- Valida `GET /health`, `GET /presence`, `POST /command`, `GET /history` e `GET /checkpoints`.
- O estado global do `JarvisCore` e da voz e isolado durante o smoke test.
- O smoke test pula automaticamente quando dependencias web ou sockets locais nao estao disponiveis.
- Smoke test validado fora do sandbox com sockets localhost permitidos.

### Fase 3U - Smoke HTTP De Sessao E Eventos

Status: concluida.

Entregas:
- Smoke HTTP expandido para validar `POST /pause` e `POST /resume` atravessando o servidor local real.
- Validacao de `GET /presence` depois de pausar e retomar, cobrindo `status` e `voice_listening`.
- Smoke HTTP agora confirma um checkpoint via `POST /command` com `confirm_actions=true`.
- Validacao de eventos recentes por `GET /checkpoints`, incluindo bloqueio por `shell_disabled`.
- Cobertura preserva a regra de seguranca: checkpoint sensivel continua pendente quando shell esta bloqueado.

### Fase 3V - Contrato Agregado Para UI Desktop

Status: concluida.

Entregas:
- Novo modulo `ui_state` para montar um contrato estavel para interfaces locais.
- Novo endpoint `GET /ui/state` com `schema_version`, presenca, checkpoints, historico curto, privacidade e proximas acoes.
- O contrato evita acionar skills e nao altera memoria ao ser consultado.
- Proximas acoes priorizam confirmacao de checkpoints pendentes antes das sugestoes gerais.
- Testes unitarios para o builder de UI state.
- Teste de contrato da API para `GET /ui/state`.

### Fase 3W - Preview CLI Do Estado De UI

Status: concluida.

Entregas:
- Novo formatador `format_ui_state` para exibir o contrato agregado no terminal.
- Novo comando `python -m app.cli ui-state`.
- Novo target `make ui-state`.
- Chat interativo ganhou `/ui-state` e atalho `/ui`.
- Preview mostra schema, presenca, checkpoints, privacidade, historico curto e proximas acoes.
- Testes cobrindo formatador, comando CLI, acao do chat e atalho.

### Fase 3X - Interface Web Local Inicial

Status: concluida.

Entregas:
- Novo modulo `ui_frontend` para servir arquivos locais da interface.
- Novo endpoint `GET /ui` com a primeira interface visual local do J.A.R.V.I.S.
- Novo endpoint `GET /ui/assets/{asset_name}` com whitelist para `app.js` e `styles.css`.
- Interface consome `GET /ui/state` e atualiza estado periodicamente.
- Formulario de comando por texto com opcoes de confirmacao sensivel e modo privado.
- Controles de pausa, retomada, atualizacao manual e confirmacao de checkpoints.
- Proximas acoes aparecem como botoes executaveis pelo usuario.
- Assets locais, sem CDN, fontes externas ou chamadas remotas.
- Testes cobrindo leitura dos assets, contrato dos endpoints da interface e smoke HTTP real para `/ui`.

### Fase 3Y - Interface Com Eventos E Refresh Configuravel

Status: concluida.

Entregas:
- Interface web agora mostra eventos recentes de checkpoints.
- Checkpoints exibem indicador simples de risco, como `confirmacao` ou `shell bloqueado`.
- Refresh automatico pode ser configurado na propria interface: manual, 5s, 15s ou 30s.
- Preferencia de refresh fica apenas no `localStorage` do navegador.
- Testes dos assets cobrem os novos elementos de eventos e refresh.

### Fase 3Z - Manifest E Atalho Desktop Local

Status: concluida.

Entregas:
- Interface web ganhou `manifest.webmanifest` local para instalacao/atalho pelo navegador.
- Icone local `icon.svg` servido pelo backend, sem asset remoto.
- Novo modulo `desktop_launcher` para gerar arquivos `.desktop`.
- Novo comando `python -m app.cli desktop-launcher`.
- Novo target `make desktop-launcher`.
- Geracao do atalho apenas imprime o conteudo por padrao ou escreve no caminho indicado por `--output`.
- Nenhuma instalacao automatica em diretorios do usuario.
- Testes cobrindo manifest, icone, geracao do `.desktop`, escrita do arquivo e CLI.

### Fase 3AA - Instalacao Confirmada Do Atalho Desktop

Status: concluida.

Entregas:
- Novo comando `python -m app.cli install-desktop-launcher`.
- Novo target `make install-desktop-launcher`.
- Instalacao exige `--confirm` antes de escrever qualquer arquivo.
- Sem `--confirm`, o comando informa destino, URL e deixa claro que nada foi escrito.
- Caminho padrao de instalacao preparado para `~/.local/share/applications/jarvis-local.desktop`.
- Suporte a `--output` para testes e instalacoes customizadas.
- Testes cobrindo modo planejado sem escrita e instalacao confirmada em caminho temporario.

### Fase 3AB - Smoke Visual Headless Da Interface

Status: concluida.

Entregas:
- Novo smoke opcional da interface web em Chromium headless.
- O teste sobe a API local, abre `GET /ui` em navegador real e captura screenshot temporario.
- Validacao confirma que o screenshot foi gerado e nao esta vazio.
- O teste pula automaticamente quando `uvicorn`, Chromium ou sockets localhost nao estao disponiveis.
- Cobertura prepara o caminho para verificacoes visuais mais ricas da interface.

### Fase 3AC - Verificacao Visual Desktop E Mobile

Status: concluida.

Entregas:
- Smoke visual agora valida DOM renderizado apos a interface consumir `GET /ui/state`.
- Validacao confirma conteudo real da UI, como status ativo, projeto, comando e privacidade.
- Captura screenshots separadas para viewport desktop e mobile.
- Teste continua opcional e pula quando Chromium, `uvicorn` ou sockets localhost nao estao disponiveis.
- Cobertura reduz risco de regressao visual basica sem adicionar dependencias novas.

### Fase 3AD - Contrato De Acoes Da UI

Status: concluida.

Entregas:
- `GET /ui/state` agora inclui `actions` estruturadas alem de `next_actions`.
- Cada acao informa `label`, `command`, `kind`, `risk`, `requires_confirmation`, `permission`, `enabled` e `reason`.
- Checkpoints viram acoes de risco medio/alto com confirmacao obrigatoria.
- Sugestoes gerais viram acoes de baixo risco.
- Interface web passa a consumir `actions` quando disponivel e preserva fallback para `next_actions`.
- Preview CLI de UI state exibe risco e necessidade de confirmacao.
- Testes cobrindo contrato agregado, API, frontend e formatador CLI.

### Fase 3AE - Relatorios De Checkpoints Com Proximo Passo

Status: concluida.

Entregas:
- `GET /checkpoints` agora inclui `summary` com pendencias, eventos bloqueados/concluidos, ultimo status e proximo passo.
- Checkpoints passam a expor `intent`, `command`, `risk`, `permission`, `severity` e `next_step`.
- Eventos recentes recebem `severity`, `message` e `next_step` legiveis.
- Interface web mostra o proximo passo no painel de presenca, checkpoints e eventos recentes.
- CLI de checkpoints exibe resumo, comando relacionado e mensagens dos eventos.
- Testes cobrindo sessao, endpoint dedicado, formatador CLI e frontend.

### Fase 3AF - Capacidades Do Projeto No Contrato De UI

Status: concluida.

Entregas:
- `GET /ui/state` agora inclui `capabilities` com comandos detectados do projeto e acoes operacionais.
- Capacidades operacionais indicam status habilitado/bloqueado e variavel de ambiente necessaria.
- O contrato informa contagem de acoes habilitadas e bloqueadas.
- Preview CLI de UI state ganhou secao `[CAPABILITIES]`.
- Interface web mostra quantidade de comandos detectados e acoes bloqueadas no painel de privacidade.
- Testes cobrindo contrato agregado, API, frontend e formatador CLI.

### Fase 3AG - Snapshot Local De Projeto

Status: concluida.

Entregas:
- `IDESkill` ganhou intent `project_state` para responder `estado do projeto`.
- Novo detector `detect_project_state` com marcadores, diretorios, arquivos relevantes e comandos detectados.
- Snapshot ignora diretorios locais/sensiveis como `.git`, `.jarvis`, `.venv`, `node_modules` e `__pycache__`.
- `GET /ui/state` inclui o snapshot dentro de `capabilities.state`.
- Interface web mostra contagem de arquivos relevantes no painel de presenca.
- Preview CLI de UI state mostra contagem de arquivos do projeto.
- Testes cobrindo NLU, core, skill de IDE, contrato de UI state, frontend e formatador CLI.

### Fase 3AH - Sugestoes Proativas Contextuais

Status: concluida.

Entregas:
- Novo modulo `proactive` para sugerir proximos passos sem executar acoes sozinho.
- Sugestoes combinam historico local recente, snapshot do projeto, marcadores e comandos detectados.
- Respostas de comando agora mesclam sugestoes das skills com sugestoes proativas globais.
- `GET /ui/state` ganhou bloco `proactive` e injeta sugestoes proativas nas acoes da interface.
- Interface web mostra a quantidade de sugestoes proativas ativas.
- Preview CLI de UI state ganhou secao `[PROACTIVE]`.
- Testes cobrindo gerador proativo, core, contrato de UI state, API, frontend e formatador CLI.

### Fase 3AI - Auditoria Filtravel Da Memoria Local

Status: concluida.

Entregas:
- `MemoryStore.audit_summary` resume a memoria local sem exportar todo o historico por padrao.
- Auditoria aceita filtros por `intent`, `skill`, `action`, `since`, `until` e limite de amostra.
- Relatorio agrega comandos por intent, skill, acao e status.
- Novo endpoint `GET /history/audit`.
- Novo comando natural `resumo da memoria`.
- CLI ganhou `memory-audit` com filtros e o chat ganhou `/memory-audit` e `/mem`.
- Novo formatador `[MEMORY AUDIT]` para terminal.
- Testes cobrindo memoria, NLU, core, API, CLI e formatador.

### Fase 3AJ - Auditoria De Memoria Na UI Local

Status: concluida.

Entregas:
- `GET /ui/state` ganhou bloco `memory_audit` com o resumo auditavel da memoria local.
- Contrato de UI informa totais, primeira/ultima memoria, agregacoes e amostra limitada.
- Interface web ganhou area de memoria com resumo e amostra local.
- Painel de privacidade mostra contagem de comandos auditados.
- Preview CLI de `ui-state` exibe `[MEMORY AUDIT]` junto do contrato agregado.
- Testes cobrindo contrato de UI state, API, frontend, CLI e formatador.

### Fase 3AK - Filtros De Auditoria Na UI Local

Status: concluida.

Entregas:
- Interface web ganhou controles para filtrar auditoria por intent, skill, acao, periodo e limite de amostra.
- Filtros chamam `GET /history/audit` diretamente sem exportar o historico completo.
- Refresh automatico preserva filtros ativos enquanto a sessao da pagina estiver aberta.
- Botao de limpeza restaura a auditoria padrao do contrato de UI.
- CSS responsivo para os controles de auditoria.
- Testes cobrindo markup, assets JS/CSS e smoke visual em Chromium.

### Fase 3AL - Exclusao Seletiva Da Memoria Local

Status: concluida.

Entregas:
- Historico e auditoria agora expõem `id` por comando para permitir alvos auditaveis.
- `MemoryStore.delete_commands` remove entradas por id ou por filtros de intent, skill, acao e periodo.
- Novo endpoint `POST /history/delete`, com seletor obrigatorio e confirmacao explicita.
- Novo comando natural `apagar comando <id>` com confirmacao obrigatoria.
- CLI ganhou `memory-delete --id <id> --confirm` e suporte a exclusao por filtros.
- Formatadores mostram ids de comandos e resultado `[HISTORY DELETE]`.
- Exclusoes seletivas confirmadas nao sao regravadas no historico local.
- Testes cobrindo memoria, NLU, core, API, CLI e formatadores.

### Fase 3AM - Exclusao Seletiva De Memoria Na UI

Status: concluida.

Entregas:
- Interface web ganhou botao para apagar uma memoria especifica exibida na amostra auditavel.
- Interface web ganhou botao para apagar memorias que correspondem ao filtro atual.
- Exclusao por filtro exige filtro ativo para evitar apagar memoria em lote por engano.
- Todas as exclusoes pela UI usam `POST /history/delete` com `confirm: true` apos confirmacao do navegador.
- A amostra da auditoria mostra o id local do comando antes da acao de apagar.
- CSS dedicado para acoes destrutivas e layout responsivo da amostra de memoria.
- Testes cobrindo markup, JS/CSS e smoke visual em Chromium.

### Fase 3AN - Politica Central De Risco

Status: concluida.

Entregas:
- Novo modulo `backend/app/risk.py` centraliza classificacao de risco por skill, acao, comando, checkpoint e capacidade.
- Acoes agora carregam metadados consistentes: `risk`, `requires_confirmation`, `permission`, `risk_reason`, `risk_category` e descricao curta.
- Checkpoints passam a herdar risco e permissao do passo pendente, inclusive comandos de shell confirmaveis.
- Sugestoes proativas classificam comandos sensiveis, como `rodar make test`, antes de aparecerem na UI.
- `GET /ui/state` expoe risco tambem nas capacidades operacionais bloqueadas ou habilitadas.
- CLI de estado mostra risco resumido nas capacidades.
- Testes dedicados cobrem comandos perigosos, exclusao de memoria, checkpoints e permissoes por alvo.

### Fase 3AO - Comandos Compostos Seguros

Status: concluida.

Entregas:
- NLU agora reconhece pedidos com mais de uma acao, como `qual o status e listar arquivos`.
- Novo intent `multi_action` preserva as etapas detectadas em ordem.
- O core executa etapas seguras de leitura e prepara etapas sensiveis sem usar confirmacao herdada por acidente.
- Resultado composto agrega etapas concluidas, etapas bloqueadas e etapas aguardando confirmacao.
- Politica de risco agrega comandos compostos pelo maior risco entre as etapas.
- Comandos compostos entram no historico como um unico pedido do usuario, mantendo detalhes por etapa em `data.steps`.
- Testes cobrem NLU composto, execucao segura, etapa sensivel e risco agregado.

### Fase 3AP - Checkpoints Para Comandos Compostos

Status: concluida.

Entregas:
- Etapas sensiveis detectadas dentro de `multi_action` agora viram checkpoints da sessao.
- Checkpoints compostos reutilizam o fluxo existente de `confirmar checkpoint <id>`.
- A sessao ganhou suporte para adicionar novos checkpoints sem apagar checkpoints pendentes anteriores.
- Resultado de comando composto informa `checkpoint_count` e `checkpoint_ids`.
- Confirmacao de checkpoint composto delega para os executores seguros ja existentes, como shell e IDE.
- Testes cobrem append de checkpoints, criacao via comando composto e confirmacao posterior.

### Fase 3AQ - Visibilidade De Checkpoints Compostos Na UI

Status: concluida.

Entregas:
- Snapshot de sessao agora preserva `source`, `index` e `step_label` dos checkpoints.
- `GET /checkpoints` e `GET /ui/state` enriquecem checkpoints com `source_label`, `step_index`, `step_label` e `checkpoint_detail`.
- Checkpoints vindos de `multi_action` aparecem como `pedido composto`, com a etapa pendente destacada.
- Interface web local mostra metadados do checkpoint, incluindo origem, etapa e comando quando houver.
- CSS dedicado para metadados de checkpoint sem alterar a estrutura principal da UI.
- Testes cobrem contrato de checkpoints compostos, estado de UI, sessão e assets frontend.

### Fase 3AR - Eventos Auditaveis De Checkpoints

Status: concluida.

Entregas:
- Eventos registrados ao confirmar checkpoints agora preservam origem, etapa, intent e comando.
- Eventos de checkpoints compostos indicam `source=multi_action`, `step_index`, `step_label` e `command`.
- `GET /checkpoints` enriquece eventos com `source_label` e `event_detail`.
- Interface web local mostra detalhes de origem/etapa também nos eventos recentes.
- Eventos bloqueados continuam sugerindo a permissao correta sem perder o contexto do pedido original.
- Testes cobrem eventos de automacao, eventos de comandos compostos, contratos de checkpoints e assets frontend.

### Fase 3AS - Revisao De Checkpoints No CLI

Status: concluida.

Entregas:
- `format_checkpoints` agora mostra detalhe, contexto, risco, permissao, comando e proximo passo dos checkpoints.
- Eventos recentes no CLI agora exibem `event_detail`, contexto, comando e proximo passo quando disponiveis.
- Resultado de comando composto no CLI mostra resumo de etapas concluidas, etapas aguardando confirmacao e checkpoints criados.
- `panel`, `checkpoints`, `ui-state` e `chat` passam a se beneficiar do mesmo formatador.
- Testes cobrem detalhes de checkpoints/eventos e resposta formatada de `multi_action`.

### Fase 3AT - Leitura Segura De Arquivos

Status: concluida.

Entregas:
- NLU reconhece `encontrar arquivo <nome>` e `ler arquivo <nome>`.
- `FileSkill` ganhou `find_file` para busca por nome/caminho dentro do workspace.
- `FileSkill` ganhou `read_file` para ler texto UTF-8, gerar resumo simples e devolver preview limitado.
- Leitura fica restrita ao workspace, ignora diretorios ocultos/cache e bloqueia arquivos grandes.
- Leitura de arquivo e busca sao classificadas como acoes locais de baixo risco.
- Sugestoes passam a incluir leitura de `README.md` quando o projeto possui esse marcador.
- Testes cobrem NLU, busca, leitura, bloqueio de path traversal e politica de risco.

### Fase 3AU - Propostas Seguras De Edicao

Status: concluida.

Entregas:
- NLU reconhece `preparar edicao arquivo <arquivo> trocar <antigo> por <novo>`.
- `FileSkill` ganhou `propose_file_edit` para preparar substituicao textual sem escrever arquivo.
- Propostas geram diff unificado com `a/<arquivo>` e `b/<arquivo>`.
- Resultado declara `writes_file: false` para deixar claro que nada foi gravado.
- Proposta fica restrita ao workspace e reutiliza bloqueios de arquivo grande e encoding nao suportado.
- Quando o trecho antigo nao existe, a resposta falha sem gerar edicao ambigua.
- Testes cobrem NLU, diff, ausencia de escrita em disco, trecho ausente e politica de risco.

### Fase 3AV - Aplicacao Confirmada De Edicoes

Status: concluida.

Entregas:
- Propostas validas de edicao agora criam checkpoint `file_edit` para aplicacao futura.
- `confirmar checkpoint <id>` delega checkpoints de edicao para `FileSkill.apply_file_edit`.
- Aplicacao reabre o arquivo, valida se o trecho antigo ainda existe e so entao grava.
- Conflitos por arquivo alterado bloqueiam a aplicacao sem escrever.
- Acoes delegadas por checkpoint agora tambem recebem metadados de risco.
- Aplicar edicao e classificado como alto risco (`file_write`) e exige confirmacao.
- Testes cobrem criacao do checkpoint, confirmacao, escrita real, remocao do checkpoint e auditoria do evento.

## Em Desenvolvimento Ativo

### Fase 3 - Assistente Local Do Computador

Status: em desenvolvimento ativo.

Objetivo:
- Tornar o J.A.R.V.I.S. util no computador antes de expandir para celular e casa.

Prioridades atuais:
- Expandir o NLU para mais comandos locais.
- Melhorar relatorios de resultado dos checkpoints e preparar contrato para UI desktop.
- Evoluir integracoes de IDE mais profundas.
- Evoluir a presenca para um indicador visual persistente de estado ativo/ouvindo/pausado.
- Tornar a memoria local mais auditavel e editavel.

Primeiras tarefas recomendadas:
- Expor diff de propostas de edicao no CLI e na UI antes da confirmacao.

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
216 tests OK
```

Observacao:
- Em Python sem dependencias web instaladas, os 10 testes de contrato da API e os smokes HTTP/visual sao pulados.
- Em ambientes que bloqueiam sockets localhost, o smoke HTTP e pulado.
- Na suite principal do projeto, a suite tem 216 testes; smokes opcionais rodam quando sockets localhost e Chromium estao disponiveis.

```bash
python -m compileall backend/app
```

Resultado esperado:

```text
sem erros de compilacao
```
