import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage

from .tools import build_tools
from pathlib import Path


load_dotenv()

class UniversalDBAgent:
    def __init__(self, provider: str = "ollama", model_name: str = "gemma4:latest",
                 api_key: str | None = None, base_url: str | None = None,
                 temperature: float | None = None, max_tokens: int | None = None,
                 db_path: str | None = None, reports_dir: str | None = None,
                 metadata_path: str | None = None, on_file_saved=None):
        self.provider = provider.lower().strip()
        self.model_name = model_name
        self.temperature = temperature if temperature is not None else 0.0
        temp = self.temperature

        match self.provider:
            case "openai":
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    raise ImportError(
                        "Provider 'openai' requires package langchain-openai. "
                        "Install it with pip install langchain-openai"
                    )
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=temp,
                    base_url=base_url or None,
                    max_tokens=max_tokens or None,
                )
            case "google" | "gemini":
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                except ImportError:
                    raise ImportError(
                        "Provider 'google' requires package langchain-google-genai. "
                        "Install it with pip install langchain-google-genai"
                    )
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=temp,
                )
            case "anthropic":
                try:
                    from langchain_anthropic import ChatAnthropic
                except ImportError:
                    raise ImportError(
                        "Provider 'anthropic' requires package langchain-anthropic. "
                        "Install it with pip install langchain-anthropic"
                    )
                self.llm = ChatAnthropic(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=temp,
                    max_tokens=max_tokens or 4096,
                )
            case "xai":
                try:
                    from langchain_xai import ChatXAI
                except ImportError:
                    raise ImportError(
                        "Provider 'xai' requires package langchain-xai. "
                        "Install it with pip install langchain-xai"
                    )
                kwargs_xai = {"model": self.model_name, "api_key": api_key, "temperature": temp}
                if base_url:
                    kwargs_xai["base_url"] = base_url
                self.llm = ChatXAI(**kwargs_xai)
            case "ollama":
                try:
                    from langchain_ollama import ChatOllama
                except ImportError:
                    raise ImportError(
                        "Provider 'ollama' requires package langchain-ollama. "
                        "Install it with pip install langchain-ollama"
                    )
                self.llm = ChatOllama(
                    model=self.model_name,
                    base_url=base_url or "http://localhost:11434",
                    temperature=temp,
                    num_ctx=8192,
                )
            case "mistral":
                try:
                    from langchain_mistralai import ChatMistralAI
                except ImportError:
                    raise ImportError(
                        "Provider 'mistral' requires package langchain-mistralai. "
                        "Install it with pip install langchain-mistralai"
                    )
                self.llm = ChatMistralAI(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=temp,
                )
            case "bedrock":
                try:
                    from langchain_aws import ChatBedrock
                except ImportError:
                    raise ImportError(
                        "Provider 'bedrock' requires package langchain-aws. "
                        "Install it with pip install langchain-aws"
                    )
                self.llm = ChatBedrock(
                    model=self.model_name,
                    temperature=temp,
                )
            case "huggingface":
                try:
                    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
                except ImportError:
                    raise ImportError(
                        "Provider 'huggingface' requires package langchain-huggingface. "
                        "Install it with pip install langchain-huggingface"
                    )
                llm = HuggingFaceEndpoint(
                    repo_id=self.model_name,
                    huggingfacehub_api_token=api_key,
                    task="text-generation",
                )
                self.llm = ChatHuggingFace(llm=llm, temperature=temp)
            case "openrouter":
                try:
                    from langchain_openrouter import ChatOpenRouter
                except ImportError:
                    raise ImportError(
                        "Provider 'openrouter' requires package langchain-openrouter. "
                        "Install it with pip install langchain-openrouter"
                    )
                self.llm = ChatOpenRouter(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=temp,
                )
            case "deepseek":
                try:
                    from langchain_deepseek import ChatDeepSeek
                except ImportError:
                    raise ImportError(
                        "Provider 'deepseek' requires package langchain-deepseek. "
                        "Install it with pip install langchain-deepseek"
                    )
                kwargs_deepseek = {"model": self.model_name, "api_key": api_key, "temperature": temp}
                if base_url:
                    kwargs_deepseek["base_url"] = base_url
                self.llm = ChatDeepSeek(**kwargs_deepseek)
            case _:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        # Resolve paths
        project_root = Path(__file__).resolve().parent.parent.parent
        resolved_db_path = Path(db_path) if db_path else project_root / "construction_company.db"
        resolved_reports_dir = Path(reports_dir) if reports_dir else project_root / "reports"

        resolved_metadata_path = Path(metadata_path) if metadata_path else project_root / "backend" / "chat" / "metadata.json"

        # Tools Registry
        self.tools = build_tools(resolved_db_path, resolved_reports_dir, resolved_metadata_path, on_file_saved=on_file_saved)

        # Execution Map to resolve string names to Python functions
        self.tools_map = {tool.name: tool for tool in self.tools}

    def run(self, user_question: str, chat_history: list) -> tuple[str, list[dict]]:
        """
        Runs the agent loop.
        Returns:
            tuple: (final_response_text, list_of_executed_tool_steps)
        """
        if not user_question.strip():
            return "Error: Empty prompt received.", []

        agent = self.llm.bind_tools(self.tools)
        chat_history.append(HumanMessage(content=user_question))

        # Track steps executed during THIS specific turn for Django
        executed_steps = []

        max_iterations = 5
        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1
                response = agent.invoke(chat_history)

                # Case A: Final text response
                if not response.tool_calls:
                    chat_history.append(response)
                    return response.content, executed_steps

                # Case B: Tool call(s) requested
                chat_history.append(response)

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call["id"]

                    if tool_name in self.tools_map:
                        actual_tool = self.tools_map[tool_name]
                        tool_output = actual_tool.invoke(tool_args)
                    else:
                        tool_output = f"Error: Tool '{tool_name}' is not registered."

                    # Document this intermediate step for our Django backend
                    executed_steps.append({
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "tool_output": tool_output,
                        "tool_call_id": tool_id
                    })

                    tool_message = ToolMessage(content=tool_output, tool_call_id=tool_id)
                    chat_history.append(tool_message)

            else:
                return "Agent Error: Maximum iterations reached.", executed_steps

        except Exception as e:
            return f"An internal routing error occurred: {str(e)}", executed_steps

    def generate_title(self, history: list) -> str:
        messages = [
            HumanMessage(content=(
                "You are a title generator. Based on the following conversation between a user and a database agent, "
                "generate a short, descriptive title (maximum 6 words, no quotes, no trailing punctuation). "
                "Respond ONLY with the title, nothing else. Use the same language as the conversation.\n\n"
                "Conversation:\n"
                + "\n".join(
                    f"{'User' if isinstance(m, HumanMessage) else 'Agent'}: {m.content[:300]}"
                    for m in history
                    if isinstance(m, (HumanMessage)) or (hasattr(m, 'type') and m.type == 'ai')
                )
            ))
        ]
        try:
            response = self.llm.invoke(messages)
            title = response.content.strip().strip('"').strip("'")
            words = title.split()
            if len(words) > 6:
                title = " ".join(words[:6])
            title = title.rstrip(".!?,;:")
            return title if title else "Chat"
        except Exception:
            return "Chat"
