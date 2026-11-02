"""Interface de linha de comando para testar o agente da Empório da Música."""

from __future__ import annotations

import sys

from agent import EmporioAgent


def main() -> None:
    print("=" * 60)
    print("  Empório da Música - Agente de Atendimento (protótipo)")
    print("=" * 60)
    print("Digite sua mensagem e pressione Enter.")
    print("Comandos: /sair, /exit, /quit, /ajuda, /help")
    print("-" * 60)

    agent = EmporioAgent()

    while True:
        try:
            user_input = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAté logo! 👋")
            break

        if not user_input:
            continue

        if user_input.lower() in {"/sair", "/exit", "/quit"}:
            print("\nAté logo! 👋")
            break

        if user_input.lower() in {"/ajuda", "/help"}:
            print("\n Exemplos do que você pode perguntar:")
            print("   • 'Qual o preço da guitarra Yamaha FG800?'")
            print("   • 'Tem violão Tagima em estoque?'")
            print("   • 'Qual o status do pedido #1?'")
            print("   • 'Qual o horário de funcionamento?'")
            print("   • 'Como funciona a política de troca?'")
            print("   • 'Aceitam pix?'")
            continue

        resposta = agent.respond(user_input)
        print(f"\n{agent.__class__.__name__}: {resposta}")


if __name__ == "__main__":
    main()
