from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.desk.calls import (
    CALLS,
    MEMO_PROMPT,
    MODEL_ID,
    MODEL_LICENSE,
    MODEL_WEIGHTS_URL,
    PRECOMPUTED_DRAFT,
    SYSTEM_PROMPT,
)
from app.desk.glm import GlmClient, glm_status, resolve_glm_endpoint

router = APIRouter()

_PRECOMPUTED_LABEL = (
    "Precomputed draft — no GLM_API_KEY / OPENROUTER_API_KEY / ZAI_API_KEY. "
    "Not a live GLM-5.2 call. Prompt and model id below are the live path."
)


def get_glm_client() -> GlmClient | None:
    """Live GLM client, or None when no key is set. Overridden in tests."""
    endpoint = resolve_glm_endpoint()
    if endpoint is None:
        return None
    return GlmClient(httpx.Client(), endpoint)


def _payload(*, source: str, draft: str, label: str, status: dict) -> dict:
    return {
        "model_id": MODEL_ID,
        "model_license": MODEL_LICENSE,
        "weights_url": MODEL_WEIGHTS_URL,
        "source": source,
        "label": label,
        "draft": draft,
        "prompt": MEMO_PROMPT,
        "system_prompt": SYSTEM_PROMPT,
        "live_available": status["live_available"],
        "key_name": status["key_name"],
        "request_model": status["request_model"],
        "human_owns_call": True,
    }


@router.get("/api/desk")
def get_desk() -> dict:
    status = glm_status()
    return {
        "model_id": MODEL_ID,
        "model_license": MODEL_LICENSE,
        "weights_url": MODEL_WEIGHTS_URL,
        "live_available": status["live_available"],
        "key_name": status["key_name"],
        "request_model": status["request_model"],
        "prompt": MEMO_PROMPT,
        "system_prompt": SYSTEM_PROMPT,
        "calls": CALLS,
        "human_owns_call": True,
        "precomputed": _payload(
            source="precomputed",
            draft=PRECOMPUTED_DRAFT,
            label=_PRECOMPUTED_LABEL,
            status=status,
        ),
    }


@router.post("/api/desk/memo")
def draft_memo(glm: GlmClient | None = Depends(get_glm_client)) -> dict:
    status = glm_status()
    if glm is None:
        return _payload(
            source="precomputed",
            draft=PRECOMPUTED_DRAFT,
            label=_PRECOMPUTED_LABEL,
            status=status,
        )
    try:
        text = glm.complete(MEMO_PROMPT)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GLM-5.2 request failed: {exc}",
        ) from exc
    if not (text or "").strip():
        raise HTTPException(status_code=502, detail="GLM-5.2 returned an empty draft")
    return _payload(
        source="live",
        draft=text,
        label=f"Live GLM-5.2 draft ({MODEL_ID})",
        status=status,
    )
