import re

# Regra simples de NLU baseada em palavras-chave

def parse_intent(text: str):
    if not text:
        return {"intent": "none", "text": text}
    t = text.lower()
    # Ligar / acender
    if any(w in t for w in ["ligar", "acender", "ligue", "liga", "turn on"]):
        target = None
        # detectar dispositivo simples
        if "luz" in t or "luzes" in t:
            target = "light"
        m = re.search(r"luz(?:es)? (?:da|do|de|no|na)?\s*(\w+)", t)
        return {"intent": "turn_on", "device": target, "text": text}
    # Desligar
    if any(w in t for w in ["desligar", "apagar", "desliga", "turn off"]):
        target = None
        if "luz" in t:
            target = "light"
        return {"intent": "turn_off", "device": target, "text": text}
    # Status
    if any(w in t for w in ["status", "estado", "está", "esta"]):
        return {"intent": "status", "text": text}
    # Default
    return {"intent": "unknown", "text": text}
