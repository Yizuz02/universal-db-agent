from django.db import transaction
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage
from settings_panel.models import SystemConfiguration, UserPreference
from .agent import UniversalDBAgent
from .models import Conversation, Message, MessageToolCall, GeneratedFile
import logging
import os

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent.parent.parent

def rebuild_langchain_history(conversation_instance):
    """Retrieves long-term history from Django DB and maps it to LangChain objects."""
    db_messages = Message.objects.filter(
        conversation=conversation_instance
    ).order_by('created_at')

    langchain_history = []

    for msg in db_messages:
        if msg.role == 'user':
            langchain_history.append(HumanMessage(content=msg.content))
        elif msg.role == 'agent':
            langchain_history.append(AIMessage(content=msg.content))

    return langchain_history

def execute_agent_and_save_workflow(conversation, user_text):
    """Executes the AI Agent within a safe database transaction block."""
    history = rebuild_langchain_history(conversation)

    # Resolve the active credential: prefer user's active credential, fall back to system config
    pref = UserPreference.objects.filter(user=conversation.user).first()
    cred = pref.active_credential if pref else None

    if cred:
        provider = cred.provider_type
        model_name = cred.model
        api_key = cred.get_api_key() or None
        base_url = cred.base_url or None
        temperature = cred.temperature
        max_tokens = cred.max_tokens or None
    else:
        sys_config = SystemConfiguration.get_solo()
        provider = sys_config.llm_provider
        model_name = sys_config.model_name
        api_key = None
        base_url = None
        temperature = sys_config.temperature
        max_tokens = None

    sys_config = SystemConfiguration.get_solo()

    # Resolve db_path and reports_dir
    if Path(sys_config.target_db_path).is_relative_to(project_root):
        resolved_db_path = project_root / sys_config.target_db_path
    else:
        resolved_db_path = Path(sys_config.target_db_path)
    resolved_reports_dir = project_root / "reports"

    collected_paths = []

    agent = UniversalDBAgent(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        db_path=resolved_db_path,
        reports_dir=resolved_reports_dir,
        metadata_path=project_root / "backend" / "chat" / "metadata.json",
        on_file_saved=collected_paths.append
    )

    # Run the reasoning loop
    agent_response, execution_steps = agent.run(user_text, history)


    with transaction.atomic():
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_text
        )

        for step in execution_steps:
            intent_message = Message.objects.create(
                conversation=conversation,
                role='agent',
                content=f"Thinking... Planning to invoke tool: '{step['tool_name']}'",
                has_tool_calls=True
            )
            MessageToolCall.objects.create(
                message=intent_message,
                tool_name=step["tool_name"],
                tool_args=step["tool_args"],
                tool_output=step["tool_output"],
                tool_call_id=step["tool_call_id"]
            )

        final_agent_message = Message.objects.create(
            conversation=conversation,
            role='agent',
            content=agent_response,
            has_tool_calls=False
        )

        generated_file_ids = []
        for path in collected_paths:
            try:
                filename = os.path.basename(path)
                extension = os.path.splitext(path)[1].lstrip('.')
                size = os.path.getsize(path)
                gf = GeneratedFile.objects.create(
                    message=final_agent_message,
                    conversation=conversation,
                    filename=filename,
                    extension=extension,
                    file_path=path,
                    size_bytes=size,
                )
                generated_file_ids.append(gf.id)
            except Exception:
                logger.warning("Failed to create GeneratedFile record for %s", path, exc_info=True)

        conv = Conversation.objects.get(id=conversation.id)
        user_msg_count = conv.messages.filter(role='user').count()
        default_title = "New Database Chat"
        if (
            user_msg_count >= 2
            and conv.title == default_title
            and not conv.title_edited
        ):
            try:
                full_history = rebuild_langchain_history(conv)
                new_title = agent.generate_title(full_history)
                if new_title:
                    conv.title = new_title
                    conv.save(update_fields=['title'])
                    return agent_response, new_title, generated_file_ids
            except Exception:
                logger.warning("Auto-title generation failed", exc_info=True)

    return agent_response, None, generated_file_ids
