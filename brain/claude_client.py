import json
from typing import Any

import aiohttp
from anthropic import AsyncAnthropic
from playwright.async_api import async_playwright

from config import get_settings


class ClaudeClient:
    """Claude client with provider abstraction.

    Supported modes:
    - anthropic (official SDK)
    - puter_js (browser-executed Puter.js chat)
    - openai_compatible (generic HTTP API for compatible gateways)
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = self.settings.ai_provider.lower().strip()
        self.model = self.settings.ai_model

        self._anthropic_client = None
        if self.provider == "anthropic":
            self._anthropic_client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)

    async def healthcheck(self) -> bool:
        if self.provider == "anthropic":
            return bool(self.settings.anthropic_api_key)

        if self.provider == "openai_compatible":
            return bool(self.settings.ai_base_url and self.settings.openai_compatible_api_key)

        if self.provider == "puter_js":
            return bool(self.settings.puter_script_url)

        return False

    async def generate_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
        if self.provider == "anthropic":
            if not self._anthropic_client:
                raise RuntimeError("Anthropic client is not initialized")

            response = await self._anthropic_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            chunks = [part.text for part in response.content if getattr(part, "type", None) == "text"]
            return "".join(chunks).strip()

        if self.provider == "puter_js":
            combined_prompt = (
                "SYSTEM INSTRUCTIONS:\n"
                f"{system_prompt}\n\n"
                "USER REQUEST:\n"
                f"{user_prompt}"
            )
            return await self._generate_text_puter_js(combined_prompt)

        if self.provider == "openai_compatible":
            return await self._generate_text_openai_compatible(system_prompt, user_prompt, max_tokens)

        raise ValueError(f"Unsupported AI provider: {self.provider}")

    async def _generate_text_puter_js(self, prompt: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await page.goto("about:blank", wait_until="load")
                await page.add_script_tag(url=self.settings.puter_script_url)

                result = await page.evaluate(
                    """
                    async ({prompt, model}) => {
                        if (!globalThis.puter || !globalThis.puter.ai || !globalThis.puter.ai.chat) {
                            throw new Error('Puter.js failed to initialize or API unavailable');
                        }

                        const response = await globalThis.puter.ai.chat(prompt, { model });

                        const maybeText = response?.message?.content?.[0]?.text;
                        if (typeof maybeText === 'string' && maybeText.length > 0) {
                            return maybeText;
                        }

                        if (typeof response?.text === 'string' && response.text.length > 0) {
                            return response.text;
                        }

                        return JSON.stringify(response);
                    }
                    """,
                    {"prompt": prompt, "model": self.model},
                )
                return str(result).strip()
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"puter_js request failed: {exc}") from exc
            finally:
                await context.close()
                await browser.close()

    async def _generate_text_openai_compatible(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> str:
        if not self.settings.ai_base_url:
            raise RuntimeError("AI_BASE_URL must be set for openai_compatible provider")
        if not self.settings.openai_compatible_api_key:
            raise RuntimeError(
                "OPENAI_COMPATIBLE_API_KEY must be set for openai_compatible provider"
            )

        endpoint = self.settings.ai_base_url.rstrip("/") + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_compatible_api_key}",
            "Content-Type": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=self.settings.puter_timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(endpoint, headers=headers, json=payload) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise RuntimeError(f"openai_compatible request failed: {response.status} {text}")

                data = await response.json()
                choice = (data.get("choices") or [{}])[0]
                message = choice.get("message") or {}
                content = message.get("content", "")

                if isinstance(content, list):
                    return "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part) for part in content
                    ).strip()

                if isinstance(content, str):
                    return content.strip()

                return json.dumps(content)
