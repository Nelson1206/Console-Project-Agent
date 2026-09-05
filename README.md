# Console Project Agent

A stdin/stdout app that uses LangChain + LangGraph and a local Ollama model to manage a project list stored in JSON.

## Requirements

- Python 3.12
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

Type natural language at the `> ` prompt. Type `quit` or `exit` to leave.

Projects are saved to `data/projects.json`. If that file is missing it is treated as an empty list. If it is corrupt, the app reports an English error and does not overwrite it.

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


1. `classify` routes the line to `create`, `list`, `get`, `update`, `delete`, `exit`, or `unknown`.
2. `create` goes to `extract_slots`. Required fields are `project_name` and `customer`. Optional fields (`start_date`, `location`, `status`, `notes`) are stored only if they appear in the sentence. Missing required fields are listed in one follow-up; a later line can fill them. Any new intent cancels an unfinished draft.
3. `list` reads `data/projects.json` and prints a numbered list, or says that no projects exist.
4. `get` / `update` / `delete` look up by project name (case-insensitive). One match runs the action. Several matches are disambiguated by number. Zero matches return `No project named "..." was found.` Delete does not ask for confirmation.
5. `unknown` explains the available actions. `quit` / `exit` print `Goodbye.` and end the process.

Successful creates, updates, and deletes are written immediately to JSON. The chat model is served by local Ollama.
