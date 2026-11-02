"""Testes rápidos do agente da Empório da Música."""

from agent import EmporioAgent
from intent_router import classify

a = EmporioAgent()

tests = [
    ("oi", "GREETING"),
    ("olá, tudo bem?", "GREETING"),
    ("qual o preço da guitarra Yamaha FG800?", "PRODUCT_INFO"),
    ("tem violão tagima em estoque?", "PRODUCT_INFO"),
    ("qual o preço do violão Martin D-28?", "PRODUCT_INFO"),
    ("qual o status do pedido #1?", "ORDER_STATUS"),
    ("pedido 5 rastreio", "ORDER_STATUS"),
    ("qual o horário de funcionamento?", "POLICY"),
    ("como funciona a política de troca?", "POLICY"),
    ("aceitam pix?", "POLICY"),
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
