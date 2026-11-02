"""Roteador de intenção do agente da Empório da Música.

Classifica a mensagem do cliente em uma das intenções:
  GREETING, PRODUCT_INFO, ORDER_STATUS, POLICY, OUT_OF_SCOPE, UNKNOWN.

Também extrai entidades simples (ID de pedido, nome de produto, tópico de política)
usando regras baseadas em palavras-chave e expressões regulares.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Intent:
    name: str
    confidence: float = 1.0
    entities: dict[str, str] | None = None

    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


# Palavras-chave por intenção -------------------------------------------------
GREETING_KEYWORDS = [
    "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite", "e ai", "e aí",
    "fala", "saudacao", "saudações", "alguem", "alguém",
]

PRODUCT_KEYWORDS = [
    "produto", "preço", "preco", "valor", "custa", "custam", "quanto",
    "disponível", "disponivel", "estoque", "tem", "vende", "venda",
    "guitarra", "violão", "violao", "baixo", "bateria", "teclado",
    "piano", "ukulele", "saxofone", "trompete", "violino", "corda",
]

ORDER_KEYWORDS = [
    "pedido", "rastreio", "rastreamento", "entrega", "status",
    "meu pedido", "chega", "entregue", "atrasado", "numero do pedido",
    "número do pedido", "codigo de rastreio", "código de rastreio",
]

POLICY_KEYWORDS = [
    "troca", "devolucao", "devolução", "pagamento", "pix", "cartao",
    "cartão", "boleto", "parcelar", "parcelamento", "juros",
    "horario", "horário", "funcionamento", "abre", "fecha",
    "garantia", "frete", "privacidade", "lgpd", "desconto",
    "promocao", "promoção", "política", "politica",
]

# Termos que indicam fora de escopo (acessórios que a loja não vende)
OUT_OF_SCOPE_KEYWORDS = [
    "cordas", "palheta", "palhetas", "cabo", "cabos", "case", "cases",
    "pedal", "pedais", "amplificador", "amplificadores", "afinador",
    "capotraste", "baqueta", "baquetas", "partitura",
]

ORDER_ID_RE = re.compile(r"(?:pedido|#|numero|número|ordem)?\s*#?\s*(\d{1,6})\b", re.IGNORECASE)


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def _extract_order_id(text: str) -> Optional[str]:
    m = ORDER_ID_RE.search(text)
    if m:
        return m.group(1)
    # Também aceita número puro isolado
    tokens = text.split()
    for tok in tokens:
        if tok.isdigit() and 1 <= int(tok) <= 999999:
            return tok
    return None


def _extract_topic(text: str) -> str:
    """Retorna o tópico de política mais provável, ou ''."""
    topic_map = [
        ("horario", ["horario", "horário", "funcionamento", "abre", "fecha"]),
        ("troca", ["troca", "devolucao", "devolução"]),
        ("pagamento", ["pagamento", "pix", "cartao", "cartão", "boleto", "parcel"]),
        ("garantia", ["garantia"]),
        ("frete", ["frete", "entrega"]),
        ("privacidade", ["privacidade", "lgpd", "dados"]),
        ("desconto", ["desconto", "promocao", "promoção"]),
    ]
    for topic, kws in topic_map:
        if any(kw in text for kw in kws):
            return topic
    return ""


def classify(text: str) -> Intent:
    """Classifica o texto do cliente e retorna um Intent."""
    t = text.strip().lower()
    if not t:
        return Intent("UNKNOWN", 0.0, {})

    # Saudações
    if _contains_any(t, GREETING_KEYWORDS) and len(t.split()) <= 6:
        return Intent("GREETING", 0.9, {})

    # Fora de escopo tem prioridade sobre produto (ex.: "cordas de guitarra")
    if _contains_any(t, OUT_OF_SCOPE_KEYWORDS):
        entities = {"item": _extract_item_name(t)}
        return Intent("OUT_OF_SCOPE", 0.9, entities)

    # Status de pedido
    if _contains_any(t, ORDER_KEYWORDS):
        order_id = _extract_order_id(t)
        entities: dict[str, str] = {}
        if order_id:
            entities["order_id"] = order_id
        return Intent("ORDER_STATUS", 0.85, entities)

    # Política
    if _contains_any(t, POLICY_KEYWORDS):
        topic = _extract_topic(t)
        entities = {}
        if topic:
            entities["topic"] = topic
        return Intent("POLICY", 0.85, entities)

    # Produto
    if _contains_any(t, PRODUCT_KEYWORDS):
        entities = {"query": _extract_product_query(text)}
        return Intent("PRODUCT_INFO", 0.8, entities)

    return Intent("UNKNOWN", 0.4, {})


def _extract_item_name(text: str) -> str:
    """Extrai o nome do item mencionado (para fora de escopo)."""
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if kw in text:
            return kw
    return ""


def _extract_product_query(text: str) -> str:
    """Extrai um termo de busca de produto a partir do texto."""
    t = text.strip().lower()
    # Remove pontuação
    t = re.sub(r"[^\w\sá-ú]", " ", t)
    # Remove palavras comuns que não são do produto
    stop = ["qual", "o", "a", "os", "as", "preço", "preco", "valor", "custa",
            "custam", "quanto", "tem", "disponível", "disponivel", "estoque",
            "vende", "venda", "produto", "de", "do", "da", "dos", "das",
            "em", "no", "na", "quer", "saber", "sobre", "me", "diga", "meu",
            "minha", "informacoes", "informações", "detalhes"]
    words = [w for w in t.split() if w not in stop and len(w) > 2]
    if words:
        return " ".join(words)
    return t
