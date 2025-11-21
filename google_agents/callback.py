from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types  # For types.Content


async def agent_input_check_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Logs entry and checks 'skip_llm_agent' in session state.
    If True, returns Content to skip the agent's execution.
    If False or not present, returns None to allow execution.
    """
    name = callback_context.agent_name
    print(f"\n[Callback] Entering agent: {name}, {callback_context.user_content.role}")
    for part in callback_context.user_content.parts:
        print(f"\t{part}")
