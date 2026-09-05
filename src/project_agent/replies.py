"""Fixed English replies from spec.md section 5."""

from __future__ import annotations

from project_agent.models import OPTIONAL_FIELDS, Project

FOLLOWUP_BOTH = "I still need the project name and the customer to create this project."
FOLLOWUP_CUSTOMER = "I still need the customer name for this project."
FOLLOWUP_NAME = "I still need the project name for this project."
LIST_EMPTY = "No projects found. Create one by describing it in natural language."
UNKNOWN = (
    "I didn't understand that. You can create, list, show, update, or delete "
    "projects. Type quit or exit to leave."
)
GOODBYE = "Goodbye."
STORAGE_READ_ERROR = "I could not read the project data file. It may be corrupt."
STORAGE_WRITE_ERROR = "I could not save the project. The data file may be corrupt."
OLLAMA_UNREACHABLE = (
    "I could not reach Ollama at the configured URL. Start Ollama and try again."
)
OLLAMA_MODEL_MISSING = (
    "I could not load the configured Ollama model. "
    "Pull the model named in LLM_MODEL and try again."
)
OLLAMA_ERROR = "The language model request failed. Please try again."


def created(project_name: str, customer: str) -> str:
    return f'Done. Created project "{project_name}" for customer {customer}.'


def followup(missing_fields: list[str]) -> str:
    missing = [field for field in ("project_name", "customer") if field in missing_fields]
    if missing == ["project_name", "customer"]:
        return FOLLOWUP_BOTH
    if missing == ["customer"]:
        return FOLLOWUP_CUSTOMER
    if missing == ["project_name"]:
        return FOLLOWUP_NAME
    return FOLLOWUP_BOTH


def listed(projects: list[Project]) -> str:
    if not projects:
        return LIST_EMPTY
    lines = [f"Here are your projects ({len(projects)}):"]
    for index, project in enumerate(projects, start=1):
        line = f"{index}. {project.project_name} — customer: {project.customer}"
        extras = [
            f"{field}={getattr(project, field)}"
            for field in OPTIONAL_FIELDS
            if getattr(project, field)
        ]
        if extras:
            line = f"{line} ({', '.join(extras)})"
        lines.append(line)
    return "\n".join(lines)
