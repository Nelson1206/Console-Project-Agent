"""Short English prompts for classify and slot extraction."""

CLASSIFY_SYSTEM = """Classify the user message into exactly one intent.
Allowed intents: create, list, get, update, delete, exit, unknown.
- create: add a new project
- list: show all projects
- get: show one existing project
- update: change fields on an existing project
- delete: remove an existing project
- exit: the user wants to quit
- unknown: anything else
Return only the intent. Do not invent a project action."""

EXTRACT_SYSTEM = """Extract project fields from the user message.
Fields:
- project_name (required when creating)
- customer (required when creating)
- start_date, location, status, notes (optional)
Use null when a field is not clearly present. Do not invent values.
If the user is only filling one missing field, put that value in the matching field."""
