"""Interface de linha de comando para testar o agente da Empório da Música."""

from __future__ import annotations

import argparse
import sys

from agent import EmporioAgent
from conversation_history import ConversationHistory
from data_loader import DATA_DIR, PDF_FILE
from ollama_client import OllamaClient


def _print_status(agent: EmporioAgent, history: ConversationHistory) -> None:
    status = agent.status()
    print("\nStatus do agente:")
    print(f"  Modo: {status['mode']}")
    if status["ollama_model"]:
        print(f"  Modelo: {status['ollama_model']}")
    print(f"  Diretório de dados: {DATA_DIR}")
    print(f"  PDF de políticas: {PDF_FILE} ({'carregado' if status['policies_loaded'] else 'ausente'})")
    print(f"  Produtos: {status['products']}")
    print(f"  Pedidos: {status['orders']}")
    print(f"  Histórico: {history.count()} troca(s)")


def _check_data(agent: EmporioAgent) -> int:
    status = agent.status()
    required = ("categories", "customers", "orders", "order_items", "products")
    missing = [key for key in required if not status[key]]
    if missing or not status["policies_loaded"]:
        print("Falha na validação dos dados.")
        if missing:
            print(f"  Tabelas vazias: {', '.join(missing)}")
        if not status["policies_loaded"]:
            print("  Manual de políticas ausente ou sem texto extraível.")
        return 1
    print("Validação concluída: dados CSV e manual de políticas carregados.")
    print(f"  Produtos: {status['products']} | Pedidos: {status['orders']}")
    return 0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Empório da Música customer service agent")
    parser.add_argument(
        "--ollama",
        action="store_true",
        help="use a local Ollama model to rewrite grounded responses",
    )
    parser.add_argument(
        "--ollama-model",
        default=None,
        help="Ollama model name (default: OLLAMA_MODEL or llama3.2:latest)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate local data and exit",
    )
    args = parser.parse_args()

    ollama_client = OllamaClient(model=args.ollama_model) if args.ollama else None
    agent = EmporioAgent(ollama_client=ollama_client)

    if args.check:
        raise SystemExit(_check_data(agent))

    history = ConversationHistory()
    print("=" * 60)
    print("  Empório da Música - Agente de Atendimento (protótipo)")
    print("=" * 60)
    print("Digite sua mensagem e pressione Enter.")
    print("Comandos: /sair, /exit, /quit, /ajuda, /help, /historico, /limpar, /status, /debug")
    print("-" * 60)

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

        if user_input.lower() == "/status":
            _print_status(agent, history)
            continue

        if user_input.lower() == "/historico":
            recent = history.get_recent()
            if not recent:
                print("\nNenhuma interação registrada.")
            else:
                print("\nHistórico recente:")
                for record in recent:
                    print(f"- Você: {record['user']}")
                    print(f"  Agente: {record['agent']}")
            continue

        if user_input.lower() == "/limpar":
            history.clear()
            print("\nHistórico limpo.")
            continue

        if user_input.lower().startswith("/debug "):
            debug_text = user_input[7:].strip()
            if not debug_text:
                print("\nUse /debug seguido de uma pergunta.")
                continue
            intent = agent.classify(debug_text)
            print(
                f"\nIntenção: {intent.name}\n"
                f"Confiança: {intent.confidence:.2f}\n"
                f"Entidades: {intent.entities}"
            )
            continue

        resposta = agent.respond(user_input)
        history.add(user_input, resposta)
        print(f"\n{agent.__class__.__name__}: {resposta}")


if __name__ == "__main__":
    main()
