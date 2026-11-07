from .chatbot import ReCoverChatbot

def run_cli():
    print("=" * 60)
    print("Initializing ReCover Assistant (Local Test Session)...")
    print("Type 'exit' to quit, 'reset' to start a new trader session.")
    print("=" * 60)

    bot = ReCoverChatbot()

    while True:
        try:
            msg = input("\nTrader: ").strip()
            if not msg:
                continue
            if msg.lower() == "exit":
                break
            if msg.lower() == "reset":
                bot.reset()
                print("Session reset. Conversation memory cleared.")
                continue

            result = bot.ask(msg)
            print(f"\nReCover:\n{result['answer']}")

            if result["sources"]:
                print("\nSources:")
                for s in result["sources"]:
                    print(f"  • {s['tag']} {s['reference']}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_cli()