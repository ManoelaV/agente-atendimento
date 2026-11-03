"""Testes rápidos do agente da Empório da Música."""

from agent import EmporioAgent
from conversation_history import ConversationHistory
from intent_router import classify
from knowledge_base import KnowledgeBase
from tempfile import TemporaryDirectory

a = EmporioAgent()

tests = [
    ("oi", "GREETING"),
    ("olá, tudo bem?", "GREETING"),
    ("qual o preço da guitarra Yamaha FG800?", "PRODUCT_INFO"),
    ("tem violão tagima em estoque?", "PRODUCT_INFO"),
    ("quais violões custam até R$ 1.000?", "PRODUCT_INFO"),
    ("qual o preço do violão Martin D-28?", "PRODUCT_INFO"),
    ("qual o status do pedido #1?", "ORDER_STATUS"),
    ("pedido 5 rastreio", "ORDER_STATUS"),
    ("qual o horário de funcionamento?", "POLICY"),
    ("como funciona a política de troca?", "POLICY"),
    ("aceitam pix?", "POLICY"),
    ("qual endereço da loja?", "POLICY"),
    ("garantia de quanto tempo?", "POLICY"),
    ("vocês vendem cabos?", "OUT_OF_SCOPE"),
    ("preço de palhetas?", "OUT_OF_SCOPE"),
    ("bla bla bla xyz", "UNKNOWN"),
]

ok = 0
for msg, expected in tests:
    intent = classify(msg)
    resp = a.respond(msg)
    status = "OK" if intent.name == expected else "FALHA"
    if intent.name == expected:
        ok += 1
    short = resp[:80].replace("\n", " | ")
    print(f"[{status}] {msg!r} -> {intent.name} (esperado {expected})")
    print(f"      resposta: {short}")
    print()

print(f"Acertos: {ok}/{len(tests)}")

budget_response = a.respond("Quais violões disponíveis custando até R$1000?")
assert "Tagima Memphis AC-39" in budget_response
assert "R$ 1.299,00" not in budget_response
assert "R$ 999,00" in budget_response

address_response = a.respond("qual endereço da loja?")
assert "Rua 14 de Maio, 3200" in address_response

specific_product_response = a.respond("qual o preço do violão Martin D-28?")
assert "Martin D-28" in specific_product_response
assert "R$ 11.499,00" in specific_product_response

category_response = a.respond("tem violão Tagima em estoque?")
assert "Tagima" in category_response

with TemporaryDirectory() as directory:
    history = ConversationHistory(f"{directory}/history.json")
    history.add("oi", "Olá")
    assert history.count() == 1
    assert history.get_recent(1)[0]["user"] == "oi"
    history.clear()
    assert history.count() == 0

status = KnowledgeBase().status()
assert status["products"] > 0
assert status["orders"] > 0
assert status["policies_loaded"] is True
print("Grounding, history, and data-status assertions passed")
