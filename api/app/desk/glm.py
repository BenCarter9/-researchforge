from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from app.desk.calls import MODEL_ID, SYSTEM_PROMPT

# Displayed open-weight id is always zai-org/GLM-5.2. Provider HTTP model
# strings differ; they are request-only and never replace MODEL_ID in the UI.
_OPENROUTER_REQUEST_MODEL = "z-ai/glm-5.2"
_ZAI_REQUEST_MODEL = "glm-5.2"
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_ZAI_BASE = "https://api.z.ai/api/paas/v4"


@dataclass(frozen=True)
class GlmEndpoint:
    api_key: str
    base_url: str
    request_model: str
    key_name: str


class GlmClient:
    """OpenAI-compatible chat-completions client for GLM-5.2.

    The underlying `httpx.Client` is injected so tests can use a fake with
    no network and no API key.
    """

    def __init__(self, http_client: httpx.Client, endpoint: GlmEndpoint):
        self._client = http_client
        self._endpoint = endpoint

    def complete(self, user_prompt: str) -> str:
        url = self._endpoint.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._endpoint.api_key}",
            "Content-Type": "application/json",
        }
        if self._endpoint.key_name == "OPENROUTER_API_KEY":
            headers["HTTP-Referer"] = "https://github.com/BenCarter9/-researchforge"
            headers["X-Title"] = "ResearchForge desk"
        resp = self._client.post(
            url,
            headers=headers,
            json={
                "model": self._endpoint.request_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def resolve_glm_endpoint(
    environ: dict[str, str] | None = None,
) -> GlmEndpoint | None:
    """Pick GLM_API_KEY, else OPENROUTER_API_KEY, else ZAI_API_KEY."""
    env = environ if environ is not None else os.environ
    glm_key = (env.get("GLM_API_KEY") or "").strip()
    openrouter_key = (env.get("OPENROUTER_API_KEY") or "").strip()
    zai_key = (env.get("ZAI_API_KEY") or "").strip()
    override_base = (env.get("GLM_BASE_URL") or "").strip()
    override_model = (env.get("GLM_REQUEST_MODEL") or "").strip()

    if glm_key:
        return GlmEndpoint(
            api_key=glm_key,
            base_url=override_base or _ZAI_BASE,
            request_model=override_model or _ZAI_REQUEST_MODEL,
            key_name="GLM_API_KEY",
        )
    if openrouter_key:
        return GlmEndpoint(
            api_key=openrouter_key,
            base_url=override_base or _OPENROUTER_BASE,
            request_model=override_model or _OPENROUTER_REQUEST_MODEL,
            key_name="OPENROUTER_API_KEY",
        )
    if zai_key:
        return GlmEndpoint(
            api_key=zai_key,
            base_url=override_base or _ZAI_BASE,
            request_model=override_model or _ZAI_REQUEST_MODEL,
            key_name="ZAI_API_KEY",
        )
    return None


def glm_status(environ: dict[str, str] | None = None) -> dict:
    endpoint = resolve_glm_endpoint(environ)
    return {
        "model_id": MODEL_ID,
        "live_available": endpoint is not None,
        "key_name": endpoint.key_name if endpoint else None,
        "request_model": endpoint.request_model if endpoint else None,
    }
