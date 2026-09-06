"""Ollama ChatModel factory and structured-output helpers."""

from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from project_agent import prompts
from project_agent.slots import _is_blank_slot

DEFAULT_MODEL = "llama3.2"
DEFAULT_BASE_URL = "http://localhost:11434"
ALLOWED_INTENTS = (
    "create",
    "list",
    "get",
    "update",
    "delete",
    "exit",
    "unknown",
    "follow_up",
)


class LLMError(Exception):
    """Ollama is unreachable, the model is missing, or the call failed."""

    def __init__(self, message: str, *, parse_failure: bool = False) -> None:
        super().__init__(message)
        self.user_message = message
        self.parse_failure = parse_failure


class IntentClassification(BaseModel):
    intent: Literal[
        "create", "list", "get", "update", "delete", "exit", "unknown", "follow_up"
    ]


class SlotExtraction(BaseModel):
    project_name: str | None = Field(default=None)
    customer: str | None = Field(default=None)
    start_date: str | None = Field(default=None)
    location: str | None = Field(default=None)
    status: str | None = Field(default=None)
    notes: str | None = Field(default=None)


def get_chat_model() -> ChatOllama:
    provider = (os.getenv("LLM_PROVIDER") or "ollama").strip().casefold()
    if provider != "ollama":
        raise LLMError("This application only supports Ollama. Set LLM_PROVIDER=ollama.")
    return ChatOllama(
        model=(os.getenv("LLM_MODEL") or DEFAULT_MODEL).strip(),
        base_url=(os.getenv("OLLAMA_BASE_URL") or DEFAULT_BASE_URL).strip(),
        temperature=0,
    )


def classify_with_llm(
    user_input: str,
    *,
    dialog_state: str = "idle",
    missing_fields: list[str] | None = None,
    pending_action: str = "",
) -> str:
    try:
        result = _invoke_structured(
            IntentClassification,
            prompts.classify_system(dialog_state, missing_fields, pending_action),
            user_input,
        )
    except LLMError as exc:
        if exc.parse_failure:
            return "follow_up" if dialog_state == "collecting" else "unknown"
        raise
    intent = result.intent if result.intent in ALLOWED_INTENTS else "unknown"
    if intent == "follow_up" and dialog_state != "collecting":
        return "unknown"
    return intent


def extract_with_llm(user_input: str) -> dict[str, str]:
    try:
        result = _invoke_structured(
            SlotExtraction,
            prompts.EXTRACT_SYSTEM,
            user_input,
        )
    except LLMError as exc:
        if exc.parse_failure:
            return {}
        raise
    extracted: dict[str, str] = {}
    for name in ("project_name", "customer", "start_date", "location", "status", "notes"):
        value = getattr(result, name)
        if isinstance(value, str) and value.strip() and not _is_blank_slot(value):
            extracted[name] = value.strip()
    return extracted


def _invoke_structured(schema: type[BaseModel], system_prompt: str, user_input: str) -> BaseModel:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input),
    ]
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            model = get_chat_model().with_structured_output(schema)
            return model.invoke(messages)
        except LLMError:
            raise
        except Exception as exc:
            last_error = exc
            if _is_parse_error(exc) and attempt == 0:
                continue
            if _is_parse_error(exc):
                raise LLMError(_user_message(exc), parse_failure=True) from exc
            raise LLMError(_user_message(exc)) from last_error
    raise LLMError(_user_message(last_error or Exception("LLM call failed")))


def _is_parse_error(exc: Exception) -> bool:
    text = str(exc).casefold()
    name = type(exc).__name__.casefold()
    tokens = (
        "validation",
        "parse",
        "json",
        "schema",
        "structured",
        "outputparser",
        "invalid",
        "does not match",
    )
    return any(token in text or token in name for token in tokens)


def _user_message(exc: Exception) -> str:
    text = str(exc).casefold()
    if any(token in text for token in ("connect", "connection refused", "10061", "timed out", "timeout")):
        return (
            "I could not reach Ollama at the configured URL. "
            "Start Ollama and try again."
        )
    if any(token in text for token in ("not found", "404", "no such model", "pull")):
        return (
            "I could not load the configured Ollama model. "
            "Pull the model named in LLM_MODEL and try again."
        )
    return "The language model request failed. Please try again."
