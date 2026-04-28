import asyncio
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from mcp_use import MCPAgent, MCPClient


async def run_chat():
    """Run the MCP chatbot with multiple MCP servers."""
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    # Get config file path relative to this script's location
    config_file = os.path.join(os.path.dirname(__file__), "config.json")

    print("Initializing MCP servers...")
    print("  - gtsm-db: Direct database access (read-only)")
    print("  - gtsm-api: REST API CRUD operations")

    client = MCPClient.from_config_file(config_file)
    llm = ChatGroq(model="qwen/qwen3-32b")

    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=15,
        memory_enabled=True,
    )

    print("\n===== MCP Chat =====")
    print("Connected to 2 MCP servers with 13 tools")
    print("Type 'exit' or 'quit' to end")
    print("Type 'clear' to clear history")
    print("====================\n")

    try:
        while True:
            user_input = input("\nYou: ")

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if user_input.lower() == "clear":
                agent.clear_conversation_history()
                print("History cleared.")
                continue

            print("\nAssistant: ", end="", flush=True)

            try:
                response = await agent.run(user_input)
                print(response)
            except Exception as e:
                print(f"\nError: {e}")

    finally:
        if client and client.sessions:
            await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(run_chat())
