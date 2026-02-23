from dataclasses import dataclass

from brain.claude_client import ClaudeClient
from brain.prompts import NEXUS_SYSTEM_PROMPT_TEMPLATE
from config import get_settings


@dataclass
class AskContext:
    server_name: str
    username: str
    user_id: int
    channel_id: int
    user_profile: str
    recent_messages: list[str]
    question: str


class DecisionEngine:
    """Central decision orchestration layer for NEXUS.

    For now this provides the ask/response path and creates a shared pattern
    for moderation/web-awareness decisions in subsequent steps.
    """

    def __init__(self, claude_client: ClaudeClient | None = None) -> None:
        self.settings = get_settings()
        self.claude = claude_client or ClaudeClient()

    async def answer_user_question(self, ctx: AskContext) -> str:
        system_prompt = NEXUS_SYSTEM_PROMPT_TEMPLATE.format(server_name=ctx.server_name)

        recent = "\n".join(f"- {m}" for m in ctx.recent_messages) or "- (none available)"
        user_prompt = (
            "Task: Respond to a Discord user question with concise, practical gaming advice.\n\n"
            "Available actions: respond in chat only (no moderation action for this task).\n\n"
            f"User info:\n- username: {ctx.username}\n- user_id: {ctx.user_id}\n"
            f"- channel_id: {ctx.channel_id}\n\n"
            f"User profile from memory:\n{ctx.user_profile}\n\n"
            f"Last 10 messages context:\n{recent}\n\n"
            f"User question:\n{ctx.question}\n\n"
            "Output constraints:\n"
            "- Keep response under 1400 characters.\n"
            "- Be direct and useful.\n"
            "- If uncertain, say what info is missing."
        )

        response = await self.claude.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
        return response.strip()[:1400]
