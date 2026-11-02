"""Base de conhecimento da Empório da Música.

Une os dados estruturados (CSV) com as políticas do manual (PDF) e
expõe métodos de consulta usados pelo agente de atendimento.
"""

from __future__ import annotations

import re
from typing import Any

from data_loader import load_all


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _brl(value: Any) -> str:
    total = _to_float(value)
    return f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class KnowledgeBase:
    def __init__(self, data: dict[str, Any] | None = None):
        if data is None:
            data = load_all()
        csv_data = data.get("csv", {})
        self.categories: list[dict[str, str]] = csv_data.get("categories", [])
        self.customers: list[dict[str, str]] = csv_data.get("customers", [])
        self.orders: list[dict[str, str]] = csv_data.get("orders", [])
        self.order_items: list[dict[str, str]] = csv_data.get("order_items", [])
        self.products: list[dict[str, str]] = csv_data.get("products", [])
        self.promotions: list[dict[str, str]] = csv_data.get("promotions", [])
        self.policies_text: str = data.get("policies", "")

        self._products_by_id: dict[str, dict[str, str]] = {
            str(p["product_id"]): p for p in self.products
        }
        self._products_by_name: dict[str, dict[str, str]] = {}
        for p in self.products:
            self._products_by_name[p["name"].lower()] = p
        self._orders_by_id: dict[str, dict[str, str]] = {
            str(o["order_id"]): o for o in self.orders
        }
        self._customers_by_id: dict[str, dict[str, str]] = {
            str(c["customer_id"]): c for c in self.customers
        }
        self._customers_by_name: dict[str, dict[str, str]] = {
            c["name"].lower(): c for c in self.customers
        }
        self._items_by_order: dict[str, list[dict[str, str]]] = {}
        for item in self.order_items:
            self._items_by_order.setdefault(str(item["order_id"]), []).append(item)
        self._promotions_by_product: dict[str, list[dict[str, str]]] = {}
        for promo in self.promotions:
            self._promotions_by_product.setdefault(str(promo["product_id"]), []).append(promo)

    # ------------------------------------------------------------------ #
    # Consultas de produtos
    # ------------------------------------------------------------------ #
    def find_product(self, query: str) -> dict[str, str] | None:
        """Busca um produto por ID ou por nome (contém)."""
        query = query.strip()
        if not query:
            return None
        prod = self._products_by_id.get(query)
        if prod:
            return prod
        q_lower = query.lower()
        for name, prod in self._products_by_name.items():
            if q_lower in name:
                return prod
        return None

    def product_price(self, product: dict[str, str]) -> str:
        return _brl(product.get("price_brl"))

    def product_stock(self, product: dict[str, str]) -> str:
        return str(product.get("stock_quantity", "0"))

    def product_active_promotion(self, product: dict[str, str]) -> dict[str, str] | None:
        for promo in self._promotions_by_product.get(str(product["product_id"]), []):
            if str(promo.get("is_active", "0")) == "1":
                return promo
        return None

    def product_info_message(self, product: dict[str, str]) -> str:
        name = product["name"]
        price = self.product_price(product)
        stock = self.product_stock(product)
        status = product.get("status", "active")
        desc = product.get("description", "")
        promo = self.product_active_promotion(product)
        msg = f"*{name}* — {price}\n"
        msg += f"{desc}\n"
        msg += f"Estoque: {stock} unidade(s) disponível(eis).\n"
        msg += f"Situação no catálogo: {status}.\n"
        promo = self.product_active_promotion(product)
        if promo:
            msg += (
                f"🎁 Promoção ativa: {promo['description']} — "
                f"{promo['discount_percent']}% de desconto.\n"
            )
        return msg.strip()

    # ------------------------------------------------------------------ #
    # Consultas de pedidos
    # ------------------------------------------------------------------ #
    def find_order(self, order_id: str) -> dict[str, str] | None:
        return self._orders_by_id.get(str(order_id))

    def find_customer(self, query: str) -> dict[str, str] | None:
        query = query.strip()
        if not query:
            return None
        cust = self._customers_by_id.get(query)
        if cust:
            return cust
        return self._customers_by_name.get(query.lower())

    def order_items_summary(self, order: dict[str, str]) -> list[dict[str, str]]:
        items = self._items_by_order.get(str(order["order_id"]), [])
        summary: list[dict[str, str]] = []
        for item in items:
            prod = self._products_by_id.get(str(item["product_id"]))
            if prod:
                summary.append(
                    {
                        "product_name": prod["name"],
                        "quantity": item["quantity"],
                        "unit_price": self.product_price(prod),
                    }
                )
        return summary

    def order_status_message(self, order: dict[str, str]) -> str:
        customer = self._customers_by_id.get(str(order["customer_id"]), {})
        cust_name = customer.get("name", "cliente")
        status = order.get("status", "")
        total_str = _brl(order.get("total_brl", "0"))
        tracking = order.get("tracking_code", "")
        estimated = order.get("estimated_delivery", "")

        msg = f"Olá, {cust_name}! Seu pedido #{order['order_id']} está *{status}*.\n"
        msg += f"Total: {total_str}.\n"
        if tracking:
            msg += f"Código de rastreio: {tracking}.\n"
        if estimated:
            msg += f"Previsão de entrega: {estimated}.\n"
        items = self.order_items_summary(order)
        if items:
            msg += "Itens:\n"
            for it in items:
                msg += f"• {it['quantity']}x {it['product_name']} (R$ {it['unit_price']} cada)\n"
        return msg.strip()

    # ------------------------------------------------------------------ #
    # Consultas de políticas (PDF)
    # ------------------------------------------------------------------ #
    def find_policy(self, keywords: list[str]) -> str | None:
        """Busca trechos do manual de políticas que contenham as palavras-chave."""
        if not self.policies_text:
            return None
        sections = [s.strip() for s in re.split(r"\n\s*\n", self.policies_text) if s.strip()]
        matched: list[str] = []
        for section in sections:
            sec_lower = section.lower()
            if all(kw.lower() in sec_lower for kw in keywords):
                matched.append(section)
        if not matched:
            return None
        result = "\n\n".join(matched[:3])
        return result[:2000]

    def policy_summary(self, topic: str) -> str | None:
        """Retorna um resumo de política por tópico."""
        topic_map = {
            "horario": ["horário", "funcionamento"],
            "funcionamento": ["horário", "funcionamento"],
            "troca": ["troca", "devolução"],
            "devolucao": ["troca", "devolução"],
            "devolução": ["troca", "devolução"],
            "pagamento": ["pagamento", "pix", "cartão", "boleto"],
            "pix": ["pix"],
            "cartao": ["cartão", "credito", "crédito"],
            "garantia": ["garantia"],
            "frete": ["frete", "entrega"],
            "privacidade": ["privacidade", "lgpd", "dados"],
        }
        keys = topic_map.get(topic.lower(), [topic.lower()])
        return self.find_policy(keys)

        msg = f"Olá, {cust_name}! Seu pedido #{order['order_id']} está *{status}*.\n"
        msg += f"Total: {total_str}.\n"
        if tracking:
            msg += f"Código de rastreio: {tracking}.\n"
        if estimated:
            msg += f"Previsão de entrega: {estimated}.\n"
        items = self.order_items_summary(order)
        if items:
            msg += "Itens:\n"
            for it in items:
                msg += f"• {it['quantity']}x {it['product_name']} (R$ {it['unit_price']} cada)\n"
        return msg.strip()

        msg += f"Estoque: {stock} unidade(s) disponível(eis).\n"
        msg += f"Situação no catálogo: {status}.\n"
        if promo:
            msg += (
                f" Promoção ativa: {promo['description']} — "
                f"{promo['discount_percent']}% de desconto.\n"
            )
        return msg.strip()

        for item in self.order_items:
            self._items_by_order.setdefault(str(item["order_id"]), []).append(item)
        self._promotions_by_product: dict[str, list[dict[str, str]]] = {}
        for promo in self.promotions:
            self._promotions_by_product.setdefault(str(promo["product_id"]), []).append(promo)
