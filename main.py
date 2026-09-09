import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))





from dotenv import load_dotenv

from chat.agent import UniversalDBAgent

load_dotenv()

dbAgent = UniversalDBAgent()

messages = []

print("="*60)
print(f"🏗️ Welcome to the Universal DB Inspector")
print("Type 'exit' or 'quit' to end the conversation.")
print("="*60)

while True:
    user_input = input("\n👤 User: ")
    if user_input.strip().lower() in ["exit", "quit"]:
        print("Goodbye! 🏗️")
        break
        
    if not user_input.strip():
        continue

    # Append the new human question to the global history
    response = dbAgent.run(user_input.strip(), messages)

    print(f"\n🤖 Agent: {response}")