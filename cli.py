from app.agent import ShoppingAssistantAgent
from app.config import settings
from app.memory import ConversationMemory


def main() -> None:
    settings.validate()
    memory = ConversationMemory(settings.max_history_messages)
    agent = ShoppingAssistantAgent(settings, memory)
    session_id = "cli"

    print("CompraTech iniciado. Escribe 'salir' para terminar.")
    while True:
        user_text = input("Tu: ").strip()
        if user_text.lower() in {"salir", "exit"}:
            print("CompraTech: Hasta luego.")
            break
        if not user_text:
            continue
        result = agent.chat(user_text, session_id)
        print(f"CompraTech: {result.response}")


if __name__ == "__main__":
    main()
