"""Agente de atendimento da Empório da Música.

Implementa a persona da loja, roteia intenções e gera respostas em
português do Brasil com base na base de conhecimento.
"""

from __future__ import annotations

from typing import Optional

from data_loader import load_all
from intent_router import Intent, classify
from knowledge_base import KnowledgeBase


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

    def __init__(self, kb: Optional[KnowledgeBase] = None):
        self.kb = kb or KnowledgeBase()

    # ------------------------------------------------------------------ #
    def respond(self, text: str) -> str:
        """Recebe o texto do cliente e retorna a resposta do agente."""
        intent = classify(text)

        if intent.name == "GREETING":
            return self.GREETING

        if intent.name == "PRODUCT_INFO":
            return self._handle_product(intent)

        if intent.name == "ORDER_STATUS":
            return self._handle_order(intent)

        if intent.name == "POLICY":
            return self._handle_policy(intent)

        if intent.name == "OUT_OF_SCOPE":
            return self._handle_out_of_scope(intent)

        return self.UNKNOWN

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #
    def _handle_product(self, intent: Intent) -> str:
        query = intent.entities.get("query", "")
        product = self.kb.find_product(query) if query else None
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
