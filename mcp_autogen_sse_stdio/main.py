import asyncio
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams
import os
from dotenv import load_dotenv

# Get environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")

if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is not set.")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")


async def main() -> None:

    # Setup server params for local filesystem access
    math_server = StdioServerParams(
        command="python", args=["mcp_autogen_sse_stdio/math_server.py"]
    )
    math_tools = await mcp_server_tools(math_server)

    # Setup server params for SSE access
    server_params = SseServerParams(
        url="https://rag-web-browser.apify.actor/sse",  # Updated URL to the correct endpoint
        headers={"Authorization": f"Bearer {APIFY_API_KEY}"},
        timeout=30,
    )

    # Create the tool adapter for the SSE server
    # Note: The tool adapter is created using the server_params and the tool name.
    # Ensure the tool name matches the one expected by the server
    # You may need to adjust this based on the actual tool name provided by the server
    adapter = await SseMcpToolAdapter.from_server_params(
        server_params, "rag-web-browser"
    )

    # Combine the tools from both servers into a single list
    all_tools = math_tools + [adapter]

    # Create an agent that can use the fetch tool.
    model_client = OpenAIChatCompletionClient(
        model="gpt-3.5-turbo", api_key=OPENAI_API_KEY
    )
    agent = AssistantAgent(
        name="demo_agent",
        model_client=model_client,
        tools=all_tools,
        reflect_on_tool_use=True,
    )

    await Console(
        agent.run_stream(
            task="Summarise the latest news of Iran and US negotiations in one small concise paragraph.",
            cancellation_token=CancellationToken(),
        )
    )
    await Console(
        agent.run_stream(
            task="what's (3 + 5) x 12?", cancellation_token=CancellationToken()
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
