import re
import unicodedata


LIGHT_TERMS = ("luz", "luzes", "lampada", "lampadas", "iluminacao", "light", "lights")
TURN_ON_TERMS = ("ligar", "ligue", "liga", "acender", "acenda", "turn on")
TURN_OFF_TERMS = ("desligar", "desliga", "apagar", "apague", "turn off")
STATUS_TERMS = ("status", "estado", "esta", "operacional")
LIST_FILES_TERMS = ("listar arquivos", "mostrar arquivos", "ver arquivos", "ls")
READ_FILE_TERMS = (
    "ler arquivo",
    "leia arquivo",
    "mostrar arquivo",
    "mostre arquivo",
    "resumir arquivo",
    "resuma arquivo",
    "resumo do arquivo",
    "ler",
    "leia",
    "resumir",
    "resuma",
)
FIND_FILE_TERMS = (
    "encontrar arquivo",
    "encontre arquivo",
    "localizar arquivo",
    "localize arquivo",
    "procurar arquivo",
    "procure arquivo",
    "buscar arquivo",
    "busque arquivo",
)
EDIT_FILE_TERMS = (
    "editar arquivo",
    "edite arquivo",
    "alterar arquivo",
    "altere arquivo",
    "preparar edicao",
    "preparar edição",
    "propor edicao",
    "propor edição",
)
WHERE_TERMS = ("onde estou", "onde estamos", "diretorio atual", "pasta atual", "pwd")
CAPABILITY_TERMS = ("o que voce pode controlar", "o que voce faz", "capacidades", "comandos disponiveis")
DIAGNOSTICS_TERMS = ("diagnostico", "diagnóstico", "saude do sistema", "saúde do sistema", "dependencias", "dependências")
DEPENDENCY_CHECK_TERMS = (
    "validar dependencias opcionais",
    "validar dependências opcionais",
    "checar dependencias opcionais",
    "checar dependências opcionais",
    "verificar dependencias opcionais",
    "verificar dependências opcionais",
    "dependencias opcionais",
    "dependências opcionais",
)
INSTALL_DEPENDENCIES_TERMS = (
    "instalar dependencias opcionais",
    "instalar dependências opcionais",
    "preparar dependencias opcionais",
    "preparar dependências opcionais",
    "como instalar dependencias opcionais",
    "como instalar dependências opcionais",
)
PROJECT_STATUS_TERMS = ("status do projeto", "analisar projeto", "analise o projeto", "como esta o projeto")
PREPARE_PROJECT_TERMS = ("preparar projeto", "prepara o projeto", "preparar ambiente", "prepara o ambiente")
AUTOMATION_PLAN_TERMS = ("rotina de desenvolvimento", "plano de automacao", "plano de automação", "automatizar rotina", "preparar rotina")
PROJECT_CHECKUP_TERMS = ("checkup do projeto", "check-up do projeto", "verificar projeto", "revisar projeto")
EXECUTE_AUTOMATION_PLAN_TERMS = (
    "executar rotina de desenvolvimento",
    "rodar rotina de desenvolvimento",
    "executar plano de automacao",
    "executar plano de automação",
    "rodar plano de automacao",
    "rodar plano de automação",
)
EXECUTE_PROJECT_CHECKUP_TERMS = (
    "executar checkup do projeto",
    "executar check-up do projeto",
    "rodar checkup do projeto",
    "rodar check-up do projeto",
)
RUN_TESTS_TERMS = ("rodar testes", "executar testes", "rode testes", "run tests")
OPEN_PROJECT_TERMS = ("abrir projeto", "abra o projeto", "abrir workspace", "abrir vscode", "abrir projeto no vscode")
PROJECT_COMMANDS_TERMS = ("comandos do projeto", "scripts do projeto", "listar comandos do projeto", "quais comandos do projeto")
PROJECT_STATE_TERMS = (
    "estado do projeto",
    "snapshot do projeto",
    "visao do projeto",
    "visão do projeto",
    "arquivos importantes do projeto",
    "mapear projeto",
)
HISTORY_TERMS = ("historico", "ultimos comandos", "comandos recentes")
MEMORY_AUDIT_TERMS = (
    "auditar memoria",
    "auditar memória",
    "auditoria da memoria",
    "auditoria da memória",
    "resumo da memoria",
    "resumo da memória",
    "resumo do historico",
    "resumo do histórico",
    "o que voce lembra",
)
EXPORT_HISTORY_TERMS = ("exportar historico", "exportar histórico", "backup do historico", "backup do histórico")
CLEAR_HISTORY_TERMS = ("limpar historico", "limpar histórico", "apagar historico", "apagar histórico", "esquecer historico", "esquecer histórico")
DELETE_MEMORY_TERMS = (
    "apagar comando",
    "remover comando",
    "excluir comando",
    "esquecer comando",
    "apagar memoria",
    "apagar memória",
    "remover memoria",
    "remover memória",
)
CONFIRM_CHECKPOINT_TERMS = (
    "confirmar checkpoint",
    "confirmar passo",
    "aprovar checkpoint",
    "aprovar passo",
    "executar checkpoint",
    "executar passo",
)
PENDING_CHECKPOINTS_TERMS = (
    "checkpoints pendentes",
    "listar checkpoints",
    "mostrar checkpoints",
    "ver checkpoints",
    "passos pendentes",
    "acoes pendentes",
    "ações pendentes",
)
PRIVACY_TERMS = ("privacidade", "painel de privacidade", "permissoes", "permissões", "o que voce sabe sobre mim")
MEDIA_STATUS_TERMS = ("status da midia", "status de midia", "status do audio", "status do som", "volume atual")
VOLUME_UP_TERMS = ("aumentar volume", "aumente o volume", "subir volume", "volume up")
VOLUME_DOWN_TERMS = ("diminuir volume", "diminua o volume", "baixar volume", "volume down")
MUTE_TERMS = ("mutar", "silenciar", "mute")
UNMUTE_TERMS = ("desmutar", "reativar audio", "ativar audio", "unmute")
PLAY_PAUSE_TERMS = ("pausar musica", "pausar midia", "continuar musica", "tocar musica", "play pause")
NEXT_TRACK_TERMS = ("proxima musica", "proxima faixa", "avancar faixa", "next track")
PREVIOUS_TRACK_TERMS = ("musica anterior", "faixa anterior", "voltar faixa", "previous track")
WEB_SEARCH_TERMS = ("pesquisar", "pesquise", "buscar", "busque", "procurar", "procure", "search")
OPEN_URL_TERMS = ("abrir site", "abra o site", "abrir url", "abra a url", "abrir link", "abra o link")
OPEN_APP_TERMS = ("abrir", "abra", "iniciar", "start", "open")
RUN_COMMAND_TERMS = ("rodar", "rode", "executar", "execute", "run")
COMPOSITE_CONNECTOR_PATTERN = re.compile(
    r"\s*(?:;|,|\be depois\b|\bdepois\b|\be em seguida\b|\bem seguida\b|\be tambem\b|\btambem\b|\be\s+)\s*"
)
FILLER_TERMS = (
    "jarvis",
    "por favor",
    "por gentileza",
    "agora",
    "pra mim",
    "para mim",
    "please",
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text.lower()).strip()


def _strip_fillers(text: str) -> str:
    cleaned = text
    for filler in FILLER_TERMS:
        cleaned = re.sub(rf"\b{re.escape(filler)}\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms)


def _detect_light(text: str, action: str | None = None) -> bool:
    if _has_any(text, LIGHT_TERMS):
        return True
    # Em portugues, "acender/apagar a sala" geralmente implica iluminacao.
    return action in {"turn_on", "turn_off"} and _has_any(text, ("acender", "acenda", "apagar", "apague"))


def _extract_area(text: str, has_light: bool) -> str | None:
    if has_light:
        pattern = r"\b(?:luz|luzes|lampada|lampadas|iluminacao|light|lights)\b\s*(?:da|do|de|das|dos|no|na|nos|nas)?\s*([a-z0-9 ]+)?"
        match = re.search(pattern, text)
        if match:
            area = (match.group(1) or "").strip()
            area = re.sub(r"\b(?:da|do|de|das|dos|no|na|nos|nas|a|o|as|os)\b", " ", area)
            area = _strip_fillers(area)
            if area and area not in LIGHT_TERMS:
                return area

    match = re.search(
        r"\b(?:ligar|ligue|liga|acender|acenda|desligar|desliga|apagar|apague)\b\s*(?:a|o|as|os)?\s*([a-z0-9 ]+)",
        text,
    )
    if match:
        area = _strip_fillers(match.group(1))
        if area and not _has_any(area, LIGHT_TERMS):
            return area

    return None


def _extract_open_target(text: str) -> str | None:
    match = re.search(r"\b(?:abrir|abra|iniciar|start|open)\b\s+(?:o|a|os|as)?\s*([a-z0-9_-]+)", text)
    if not match:
        return None
    return _strip_fillers(match.group(1))


def _extract_command(text: str) -> str | None:
    match = re.search(r"\b(?:rodar|rode|executar|execute|run)\b\s+(.+)", text)
    if not match:
        return None
    command = _strip_fillers(match.group(1))
    return command or None


def _extract_file_target(text: str) -> str | None:
    match = re.search(
        r"\b(?:ler|leia|mostrar|mostre|resumir|resuma|resumo|encontrar|encontre|localizar|localize|procurar|procure|buscar|busque)\b"
        r"\s+(?:\b(?:o|a|os|as)\b\s*)?(?:arquivo|documento|file)?\s*(?:chamado|chamada|nomeado|nomeada)?\s*(.+)",
        text,
    )
    if not match:
        return None
    target = _strip_fillers(match.group(1))
    target = re.sub(r"^(?:arquivo|documento|file)\s+", "", target).strip()
    return target or None


def _extract_file_edit(text: str) -> dict[str, str | None]:
    match = re.search(
        r"(?:editar|edite|alterar|altere|preparar\s+edi[cç][aã]o|propor\s+edi[cç][aã]o)"
        r".*?(?:arquivo|documento|file)\s+(.+?)\s+"
        r"(?:trocar|substituir|mudar)\s+(.+?)\s+(?:por|para)\s+(.+)$",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return {"target": None, "old_text": None, "new_text": None}
    return {
        "target": _strip_fillers(match.group(1)),
        "old_text": match.group(2).strip(),
        "new_text": match.group(3).strip(),
    }


def _extract_checkpoint_id(text: str) -> int | None:
    match = re.search(r"\b(?:checkpoint|passo)\s+(\d+)\b", text)
    if not match:
        return None
    return int(match.group(1))


def _extract_memory_command_id(text: str) -> int | None:
    match = re.search(r"\b(?:comando|memoria|memória)\s+(\d+)\b", text)
    if not match:
        return None
    return int(match.group(1))


def _extract_web_query(text: str) -> str | None:
    match = re.search(r"\b(?:pesquisar|pesquise|buscar|busque|procurar|procure|search)\b\s+(?:por|sobre|for)?\s*(.+)", text)
    if not match:
        return None
    query = _strip_fillers(match.group(1))
    return query or None


def _extract_url(text: str) -> str | None:
    match = re.search(r"\b(?:abrir site|abra o site|abrir url|abra a url|abrir link|abra o link)\b\s+(.+)", text)
    if match:
        return _strip_fillers(match.group(1))

    url_match = re.search(r"\b((?:https?://)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?)\b", text)
    if url_match:
        return url_match.group(1)
    return None


def _split_composite_text(text: str) -> list[str]:
    parts = [part.strip() for part in COMPOSITE_CONNECTOR_PATTERN.split(text) if part.strip()]
    return parts if len(parts) > 1 else []


def _parse_composite_intent(text: str, normalized: str) -> dict | None:
    parts = _split_composite_text(normalized)
    if not parts:
        return None

    steps = []
    for part in parts:
        step = parse_intent(part, allow_composite=False)
        if step.get("intent") in {"unknown", "none", "multi_action"}:
            continue
        steps.append({**step, "text": part})

    if len(steps) < 2:
        return None

    return {
        "intent": "multi_action",
        "text": text,
        "steps": steps,
        "step_count": len(steps),
    }


def parse_intent(text: str, allow_composite: bool = True):
    if not text:
        return {"intent": "none", "text": text}

    normalized = _strip_fillers(_normalize(text))
    if not normalized:
        return {"intent": "none", "text": text}

    if allow_composite:
        composite = _parse_composite_intent(text, normalized)
        if composite:
            return composite

    if _has_any(normalized, CAPABILITY_TERMS):
        return {"intent": "capabilities", "text": text}

    if _has_any(normalized, INSTALL_DEPENDENCIES_TERMS):
        return {"intent": "install_dependencies", "text": text}

    if _has_any(normalized, DEPENDENCY_CHECK_TERMS):
        return {"intent": "dependency_check", "text": text}

    if _has_any(normalized, DIAGNOSTICS_TERMS):
        return {"intent": "diagnostics", "text": text}

    if _has_any(normalized, EXPORT_HISTORY_TERMS):
        return {"intent": "export_history", "text": text}

    if _has_any(normalized, CLEAR_HISTORY_TERMS):
        return {"intent": "clear_history", "text": text}

    if _has_any(normalized, DELETE_MEMORY_TERMS):
        return {"intent": "delete_memory", "command_id": _extract_memory_command_id(normalized), "text": text}

    if _has_any(normalized, MEMORY_AUDIT_TERMS):
        return {"intent": "memory_audit", "text": text}

    if _has_any(normalized, CONFIRM_CHECKPOINT_TERMS):
        return {"intent": "confirm_checkpoint", "checkpoint_id": _extract_checkpoint_id(normalized), "text": text}

    if _has_any(normalized, PENDING_CHECKPOINTS_TERMS):
        return {"intent": "pending_checkpoints", "text": text}

    if _has_any(normalized, HISTORY_TERMS):
        return {"intent": "command_history", "text": text}

    if _has_any(normalized, PRIVACY_TERMS):
        return {"intent": "privacy_panel", "text": text}

    if _has_any(normalized, MEDIA_STATUS_TERMS):
        return {"intent": "media_control", "media_action": "status", "text": text}

    if _has_any(normalized, VOLUME_UP_TERMS):
        return {"intent": "media_control", "media_action": "volume_up", "text": text}

    if _has_any(normalized, VOLUME_DOWN_TERMS):
        return {"intent": "media_control", "media_action": "volume_down", "text": text}

    if _has_any(normalized, UNMUTE_TERMS):
        return {"intent": "media_control", "media_action": "unmute", "text": text}

    if _has_any(normalized, MUTE_TERMS):
        return {"intent": "media_control", "media_action": "mute", "text": text}

    if _has_any(normalized, NEXT_TRACK_TERMS):
        return {"intent": "media_control", "media_action": "next", "text": text}

    if _has_any(normalized, PREVIOUS_TRACK_TERMS):
        return {"intent": "media_control", "media_action": "previous", "text": text}

    if _has_any(normalized, PLAY_PAUSE_TERMS):
        return {"intent": "media_control", "media_action": "play_pause", "text": text}

    if _has_any(normalized, OPEN_URL_TERMS):
        return {"intent": "open_url", "url": _extract_url(normalized), "text": text}

    if _has_any(normalized, WEB_SEARCH_TERMS):
        return {"intent": "web_search", "query": _extract_web_query(normalized), "text": text}

    if _has_any(normalized, PROJECT_STATUS_TERMS):
        return {"intent": "project_status", "text": text}

    if _has_any(normalized, PREPARE_PROJECT_TERMS):
        return {"intent": "prepare_project", "text": text}

    if _has_any(normalized, EXECUTE_PROJECT_CHECKUP_TERMS):
        return {"intent": "execute_project_checkup", "text": text}

    if _has_any(normalized, EXECUTE_AUTOMATION_PLAN_TERMS):
        return {"intent": "execute_automation_plan", "text": text}

    if _has_any(normalized, PROJECT_CHECKUP_TERMS):
        return {"intent": "project_checkup", "text": text}

    if _has_any(normalized, AUTOMATION_PLAN_TERMS):
        return {"intent": "automation_plan", "text": text}

    if _has_any(normalized, RUN_TESTS_TERMS):
        return {"intent": "run_tests", "text": text}

    if _has_any(normalized, PROJECT_COMMANDS_TERMS):
        return {"intent": "project_commands", "text": text}

    if _has_any(normalized, PROJECT_STATE_TERMS):
        return {"intent": "project_state", "text": text}

    if _has_any(normalized, OPEN_PROJECT_TERMS):
        return {"intent": "open_project", "text": text}

    if _has_any(normalized, EDIT_FILE_TERMS):
        edit = _extract_file_edit(text)
        return {"intent": "propose_file_edit", **edit, "text": text}

    if _has_any(normalized, FIND_FILE_TERMS):
        return {"intent": "find_file", "target": _extract_file_target(normalized), "text": text}

    if _has_any(normalized, READ_FILE_TERMS):
        return {"intent": "read_file", "target": _extract_file_target(normalized), "text": text}

    if _has_any(normalized, LIST_FILES_TERMS):
        return {"intent": "list_files", "text": text}

    if _has_any(normalized, WHERE_TERMS):
        return {"intent": "where_am_i", "text": text}

    if _has_any(normalized, RUN_COMMAND_TERMS):
        return {"intent": "run_command", "command": _extract_command(normalized), "text": text}

    if _has_any(normalized, OPEN_APP_TERMS):
        return {"intent": "open_app", "target": _extract_open_target(normalized), "text": text}

    if _has_any(normalized, TURN_ON_TERMS):
        has_light = _detect_light(normalized, "turn_on")
        area = _extract_area(normalized, has_light)
        return {
            "intent": "turn_on",
            "domain": "light" if has_light else None,
            "device": "light" if has_light else None,
            "area": area,
            "text": text,
        }

    if _has_any(normalized, TURN_OFF_TERMS):
        has_light = _detect_light(normalized, "turn_off")
        area = _extract_area(normalized, has_light)
        return {
            "intent": "turn_off",
            "domain": "light" if has_light else None,
            "device": "light" if has_light else None,
            "area": area,
            "text": text,
        }

    if _has_any(normalized, STATUS_TERMS):
        return {"intent": "status", "text": text}

    return {"intent": "unknown", "text": text}
