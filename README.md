# Console Project Agent

A stdin/stdout app that uses LangChain + LangGraph and a local Ollama model to manage a project list stored in JSON.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) running locally

No cloud API key is required.

## LLM provider and model

| Item | Value |
| --- | --- |
| Provider | Ollama only |
| Verified model | `llama3.2` |
| Default URL | `http://localhost:11434` |

This project does not implement OpenRouter or any other cloud LLM path.

## Install

From the project root:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

Pull the verified model and start Ollama:

```bash
ollama pull llama3.2
ollama serve
```

Copy the example env file (optional; defaults already match the verified setup):

```bash
cp .env.example .env
```

On Windows PowerShell: `Copy-Item .env.example .env`

`.env` may contain:

```text
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
# OLLAMA_BASE_URL=http://localhost:11434
# PROJECTS_JSON_PATH=data/projects.json
```

## Run

One official command, from the project root with the virtualenv active and Ollama running:

```bash
python -m project_agent.main
```

On start the app prints a short banner and welcome text, then the `> ` prompt. Type natural language there. Type `quit` or `exit` to leave.

Projects are saved to `data/projects.json`. If that file is missing it is treated as an empty list. If it is corrupt, the app reports an English error and does not overwrite it.

## Tests

Graph route cases live under `tests/cases/`. Each folder is one LangGraph path. The runner **does not call Ollama**; classify and extract values come from the JSON case. Full usage, case schema, and how to add a case are in [`tests/README.md`](tests/README.md).

From the project root with the virtualenv active and the package installed:

```bash
python -m tests
python -m tests --list
python -m tests 01_create_complete
python -m tests --route 06_update --case unique_customer
```

Optional pytest (`pip install -e ".[test]"`):

```bash
python -m pytest
python -m pytest --route 01_create_complete
```

Reports go to `tests/reports/latest.md` and `tests/reports/latest.json` (only the cases that ran).

## LangGraph workflow

Each line of input is one LangGraph turn.

```mermaid
flowchart TD
    START([START]) --> classify

    classify -->|create / follow_up| extract_slots
    classify -->|list| list_projects
    classify -->|get / update / delete| resolve_target
    classify -->|exit| exit_node
    classify -->|unknown| clarify_message
    classify -->|LLM error| llm_error
    classify -->|valid number| action

    extract_slots -->|required fields complete| create_project
    extract_slots -->|missing required fields| ask_followup
    extract_slots -->|LLM error| llm_error

    resolve_target -->|0 matches| not_found
    resolve_target -->|1 match| action
    resolve_target -->|several matches| ask_disambiguation
    resolve_target -->|update with no fields| ask_followup
    resolve_target -->|LLM error| llm_error

    action["get_project / update_project / delete_project"]

    create_project --> END([END])
    list_projects --> END
    ask_followup --> END
    ask_disambiguation --> END
    action --> END
    not_found --> END
    clarify_message --> END
    llm_error --> END
    exit_node --> END
```


1. `classify` sends each line through the Ollama classifier, including follow-up turns. It routes to `create`, `list`, `get`, `update`, `delete`, `exit`, `follow_up`, or `unknown`. Bare values such as `Acme` stay `follow_up`; a new action or an off-topic line cancels an unfinished draft. `quit` / `exit` may be handled by the REPL before the graph; every other line, including `list projects`, is classified by the model.
2. `create` goes to `extract_slots`. Slot extraction is LLM-first. A small lock keeps the assignment phrases `called X for customer Y` and `project X for Y` (and labeled `field is/to` updates). Optional fields come from the model when they appear in the sentence. Missing required fields are listed in one follow-up; a later line can fill them. Any new intent cancels an unfinished draft.
3. `list` reads `data/projects.json` and prints a numbered list, or says that no projects exist.
4. `get` / `update` / `delete` look up by project name (case-insensitive). One match runs the action. Several matches are disambiguated by number. Zero matches return `No project named "..." was found.` Delete does not ask for confirmation.
5. `unknown` explains the available actions. `quit` / `exit` print `Goodbye.` and end the process.

Successful creates, updates, and deletes are written immediately to JSON. The chat model is served by local Ollama.

## Example sessions

These match the verified English replies. `id` values are generated at runtime and will differ on your machine.

### 1. Create and list (assignment golden path)

```text
> list projects
No projects found. Create one by describing it in natural language.

> create a project called Alpha for customer Acme
Done. Created project "Alpha" for customer Acme.

> create project Beta for Globex
Done. Created project "Beta" for customer Globex.

> list projects
Here are your projects (2):
1. Alpha — customer: Acme
2. Beta — customer: Globex

```

### 2. Missing field follow-up

```text
> create a project called Delta
I still need the customer name for this project.

> Acme
Done. Created project "Delta" for customer Acme.

> create a project called GAMMA
I still need the customer name for this project.

> the customer is Amy
Done. Created project "GAMMA" for customer Amy.
```

### 3. Update Project

```text
> update GAMMA
Multiple projects named "GAMMA" were found. Reply with a number:
1. GAMMA — customer: Amy — id: 768b5a08-c717-4041-8700-1f0418a6a25f
2. Gamma — customer: Initech — id: b3af5a37-bcff-486e-bbe9-6155261855a8
3. Gamma — customer: Initech — id: 43986c41-43aa-4a8f-bb16-92aa56f0b113

> 2                         
Which fields should I update? You can change project name, customer, start date, location, status, or notes.

> change customer to tester
Done. Updated project "Gamma" (id: b3af5a37-bcff-486e-bbe9-6155261855a8): customer -> tester

> update Beta  
Which fields should I update? You can change project name, customer, start date, location, status, or notes.

> change the location to Hong Kong
Done. Updated project "Beta" (id: 19025305-9849-4feb-9d5e-6e1d7797370d): location -> Hong Kong
```
