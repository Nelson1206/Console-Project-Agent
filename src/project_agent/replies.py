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
UNEXPECTED_ERROR = "Something went wrong. Please try again."
OLLAMA_UNREACHABLE = (
    "I could not reach Ollama at the configured URL. Start Ollama and try again."
)
OLLAMA_MODEL_MISSING = (
    "I could not load the configured Ollama model. "
    "Pull the model named in LLM_MODEL and try again."
)
OLLAMA_ERROR = "The language model request failed. Please try again."
UPDATE_WHICH_FIELDS = (
    "Which fields should I update? You can change project name, customer, "
    "start date, location, status, or notes."
)
_FIELD_DISPLAY = {
    "project_name": "project_name",
    "customer": "customer",
    "start_date": "start_date",
    "location": "location",
    "status": "status",
    "notes": "notes",
}


def created(project_name: str, customer: str, extras: dict[str, str] | None = None) -> str:
    line = f'Done. Created project "{project_name}" for customer {customer}.'
    if not extras:
        return line
    bits = [f"{key}={value}" for key, value in extras.items() if value]
    if not bits:
        return line
    return f"{line}\nAlso recorded: {', '.join(bits)}."


def not_found(name: str) -> str:
    return f'No project named "{name}" was found.'


def got(project: Project) -> str:
    lines = [
        f'Project "{project.project_name}" (id: {project.id})',
        f"customer: {project.customer}",
        f"created_at: {project.created_at}",
    ]
    for field in OPTIONAL_FIELDS:
        value = getattr(project, field)
        if value:
            lines.append(f"{field}: {value}")
    return "\n".join(lines)


def updated(project: Project, changes: dict[str, str]) -> str:
    parts = [
        f"{_FIELD_DISPLAY.get(field, field)} -> {value}"
        for field, value in changes.items()
    ]
    return (
        f'Done. Updated project "{project.project_name}" (id: {project.id}): '
        + "; ".join(parts)
    )


def deleted(project: Project) -> str:
    return (
        f'Done. Deleted project "{project.project_name}" for customer '
        f"{project.customer} (id: {project.id})."
    )


def disambiguation(name: str, matches: list[dict]) -> str:
    lines = [f'Multiple projects named "{name}" were found. Reply with a number:']
    for index, item in enumerate(matches, start=1):
        lines.append(
            f"{index}. {item['project_name']} — customer: {item['customer']} — id: {item['id']}"
        )
    return "\n".join(lines)


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
