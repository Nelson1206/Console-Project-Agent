"""Short English prompts for classify and slot extraction."""

CLASSIFY_SYSTEM = """Classify the user message into exactly one intent.
Allowed intents: create, list, get, update, delete, exit, unknown, follow_up.
- create: add a new project
- list: show all projects. Also use list when the user asks to see or create a list of projects (no new record).
- get: show one existing project by name
- update: change fields on an existing project
- delete: remove an existing project
- exit: the user wants to quit
- follow_up: the user is answering a pending question (filling a missing field, or saying which fields to change). Bare values such as a name, customer, date, location, status, or notes are follow_up.
- unknown: off-topic or unintelligible, and clearly not an answer to a pending question
A customer or project name that happens to contain a verb is not an intent.
Return only the intent. Do not invent a project action."""


def classify_system(
    dialog_state: str = "idle",
    missing_fields: list[str] | None = None,
    pending_action: str = "",
) -> str:
    extra = ""
    if dialog_state == "collecting" and pending_action == "update":
        extra = (
            "\nCurrent dialogue: waiting for fields to update on an already-selected project. "
            "If the user names fields or values to change, return follow_up (not update). "
            "Return update only if they clearly start a different update on another project."
        )
    elif dialog_state == "collecting":
        missing = ", ".join(missing_fields or []) or "required create fields"
        extra = (
            f"\nCurrent dialogue: collecting a new project. Still missing: {missing}. "
            "If the user is supplying those values, return follow_up. "
            "A bare value is follow_up, not unknown. "
            "If they start a different action, return that intent."
        )
    elif dialog_state == "disambiguating":
        extra = (
            "\nCurrent dialogue: waiting for a list number to pick a project. "
            "A new action cancels disambiguation. A number is handled before this prompt."
        )
    return CLASSIFY_SYSTEM + extra


EXTRACT_SYSTEM = """Extract project fields from the user message.
Fields:
- project_name (required when creating)
- customer (required when creating)
- start_date, location, status, notes (optional)
Use null when a field is not clearly present. Do not invent values.
If the user is only filling one missing field, put that value in the matching field."""
