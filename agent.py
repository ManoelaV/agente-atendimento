"""Agente de atendimento da Empório da Música.

Implementa a persona da loja, roteia intenções e gera respostas em
português do Brasil com base na base de conhecimento.
"""

from __future__ import annotations

from typing import Optional

from data_loader import load_all
from intent_router import Intent, classify
from knowledge_base import KnowledgeBase
from ollama_client import OllamaClient


class EmporioAgent:
    """Agente de atendimento por texto da Empório da Música."""

    NOME_LOJA = "Empório da Música"

    # Mensagens fixas da persona ------------------------------------------------
    GREETING = (
        f"Olá! Sou o atendente virtual da *{NOME_LOJA}*.\n"
        "Como posso ajudar você hoje? Posso consultar preços e estoque de "
        "instrumentos, o status do seu pedido ou tirar dúvidas sobre nossas "
        "políticas (trocas, pagamentos, horário, garantia)."
    )

    UNKNOWN = (
        "Desculpe, não entendi bem sua pergunta. \n"
        "Posso ajudar com informações sobre instrumentos musicais, pedidos, "
        "promoções e políticas da loja. Pode tentar reformular?"
    )

    OUT_OF_SCOPE = (
        "A *{nome_loja}* trabalha exclusivamente com instrumentos musicais. "
        "Não comercializamos acessórios como {item} (cordas, palhetas, cabos, "
        "cases, pedais ou amplificadores).\n"
        "Se precisar de algum instrumento, é só me dizer!"
    )

    PRODUCT_NOT_FOUND = (
        "Não encontrei esse instrumento no nosso catálogo. \n"
        "Pode confirmar o nome ou o código do produto? Caso contrário, "
        "posso sugerir categorias disponíveis."
    )

    ORDER_NOT_FOUND = (
        "Não encontrei um pedido com esse número. \n"
        "Confira o número do pedido e tente novamente."
    )

    ESCALATION = (
        "Não consigo resolver isso sozinho. Vou encaminhar para a nossa "
        "equipe de atendimento, que retorna em até 24 horas úteis. "
        "Precisa de mais alguma coisa enquanto isso?"
    )

    def __init__(
        self,
        kb: Optional[KnowledgeBase] = None,
        ollama_client: Optional[OllamaClient] = None,
    ):
        self.kb = kb or KnowledgeBase()
        self.ollama_client = ollama_client

    # ------------------------------------------------------------------ #
    def respond(self, text: str) -> str:
        """Recebe o texto do cliente e retorna a resposta do agente."""
        intent = classify(text)

        if intent.name == "GREETING":
            answer = self.GREETING
        elif intent.name == "PRODUCT_INFO":
            answer = self._handle_product(intent)
        elif intent.name == "ORDER_STATUS":
            answer = self._handle_order(intent)
        elif intent.name == "POLICY":
            answer = self._handle_policy(intent)
        elif intent.name == "OUT_OF_SCOPE":
            answer = self._handle_out_of_scope(intent)
        else:
            answer = (
                "Não tenho certeza do que você precisa. Você pode informar "
                "o nome do produto, o número do pedido ou o tema da política?"
            )

        if self.ollama_client:
            return self.ollama_client.generate(text, answer) or answer
        return answer

    def classify(self, text: str) -> Intent:
        """Expose classification for diagnostics without changing responses."""
        return classify(text)

    def status(self) -> dict[str, object]:
        """Return runtime and knowledge-base diagnostics."""
        return {
            "mode": "ollama" if self.ollama_client else "deterministic",
            "ollama_model": self.ollama_client.model if self.ollama_client else "",
            **self.kb.status(),
        }

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #
    def _handle_product(self, intent: Intent) -> str:
        query = intent.entities.get("query", "")
        max_price_text = intent.entities.get("max_price", "")
        category_id = intent.entities.get("category_id", "")
        if max_price_text:
            max_price = float(max_price_text) if max_price_text else None
            products = self.kb.find_products(
                query="",
                max_price=max_price,
                category_id=category_id,
            )
            return self.kb.product_list_message(products, max_price)
        product = self.kb.find_product(query) if query else None
        if not product and category_id:
            products = self.kb.find_products(query=query, category_id=category_id)
            return self.kb.product_list_message(products)
        if not product:
            return self.PRODUCT_NOT_FOUND
        return self.kb.product_info_message(product)

    def _handle_order(self, intent: Intent) -> str:
        order_id = intent.entities.get("order_id")
        if not order_id:
            return (
                "Para consultar o status do seu pedido, preciso do número "
                "do pedido. Ele está no comprovante ou no e-mail de "
                "confirmação. Qual é o número?"
            )
        order = self.kb.find_order(order_id)
        if not order:
            return self.ORDER_NOT_FOUND
        return self.kb.order_status_message(order)

    def _handle_policy(self, intent: Intent) -> str:
        topic = intent.entities.get("topic", "")
        policy = self.kb.policy_summary(topic) if topic else None
        if not policy:
            # Tenta buscar palavras-chave brutas do texto original
            policy = self.kb.find_policy([topic] if topic else [])
        if policy:
            return policy
        return (
            "Não encontrei essa informação no manual de políticas. \n"
            "Pode detalhar sua dúvida? Se preferir, posso encaminhar para "
            "a equipe responsável."
        )

    def _handle_out_of_scope(self, intent: Intent) -> str:
        item = intent.entities.get("item", "acessórios")
        return self.OUT_OF_SCOPE.format(
            nome_loja=self.NOME_LOJA, item=item
        )
