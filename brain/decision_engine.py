import json
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


@dataclass
class ModerationContext:
    server_name: str
    username: str
    user_id: int
    channel_id: int
    message_content: str
    user_profile: str
    recent_messages: list[str]
    server_rules: str


class DecisionEngine:
    """Central decision orchestration layer for NEXUS."""

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

    async def moderation_decision(self, ctx: ModerationContext) -> dict:
        system_prompt = NEXUS_SYSTEM_PROMPT_TEMPLATE.format(server_name=ctx.server_name)
        recent = "\n".join(f"- {m}" for m in ctx.recent_messages) or "- (none available)"

        user_prompt = (
            "Task: moderate a Discord message and return strict JSON only.\n"
            "Allowed actions: warn, mute, kick, ban, ignore.\n"
            "If confidence is low, use action=ignore and explain uncertainty.\n\n"
            f"Server rules:\n{ctx.server_rules}\n\n"
            f"User profile:\n{ctx.user_profile}\n\n"
            f"Recent channel context:\n{recent}\n\n"
            f"Target message:\n{ctx.message_content}\n\n"
            "Return JSON object exactly with keys:\n"
            "action (warn|mute|kick|ban|ignore), confidence (0-100), reason (string), duration_minutes (int)."
        )

        raw = await self.claude.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
        return self._safe_parse_moderation_json(raw)

    @staticmethod
    def _safe_parse_moderation_json(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json\n", "", 1)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {
                "action": "ignore",
                "confidence": 0,
                "reason": f"Invalid JSON from model: {raw[:500]}",
                "duration_minutes": 0,
            }

        action = str(parsed.get("action", "ignore")).lower().strip()
        if action not in {"warn", "mute", "kick", "ban", "ignore"}:
            action = "ignore"

        confidence = int(parsed.get("confidence", 0) or 0)
        confidence = max(0, min(100, confidence))
        reason = str(parsed.get("reason", "No reason provided"))
        duration_minutes = int(parsed.get("duration_minutes", 0) or 0)

        return {
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "duration_minutes": max(0, duration_minutes),
        }
