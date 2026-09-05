# Console Project Agent

## Take-Home Assignment Specification

## Overview

Build a standalone console application that uses an LLM to understand natural language and manage a simple project list. The application should classify requests into intents, execute the corresponding action, and persist project data in a JSON file.

## Objective

Build a working end-to-end console application demonstrating the use of LangChain and LangGraph to interpret natural language, route requests, and perform project management actions.

## Technology Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.10+ |
| LLM Orchestration | LangChain + LangGraph |
| LLM Provider | Cloud API (OpenRouter, etc.) or Ollama |
| Storage | JSON file |
| Interface | Console (stdin/stdout) |

## Functional Requirements

### Required Intents

- Create a project from natural language. Capture at least `project_name` and `customer`. If required fields are missing, ask follow-up questions until the project can be saved.
- List all projects in a readable format. If no projects exist, clearly inform the user.

### General Behaviour

- Run continuously until the user enters `quit` or `exit`.
- Handle unclear input gracefully without crashing.

## Bonus Features

- Support optional fields (start date, location, status, notes).
- Implement additional useful intents such as get, update, or delete project.

## Using AI Assistance

You may use AI tools (ChatGPT, Cursor, GitHub Copilot, etc.) to help you build this assignment. We are open-minded about AI-assisted development. Honesty is the best policy — clearly state what you used and how.

If you used AI, include an `AI_USAGE.md` file containing:

- The AI tool(s) used.
- The main prompts used or exported/pasted chat transcript(s).
- A brief description of how AI assisted your implementation.

Submissions that hide AI usage will be viewed less favourably than those that disclose it honestly.

## Example Console Session

```text
> create a project called Alpha for customer Acme
Done. Created project "Alpha" for customer Acme.

> create project Beta for Globex
Done. Created project "Beta" for customer Globex.

> list projects
Here are your projects (2):
1. Alpha — customer: Acme
2. Beta — customer: Globex
```

## Submission Requirements

Submit either:

- A public GitHub repository link.
- A ZIP archive containing the complete project.

Your submission should include:

- Complete source code
- `README.md`
- `AI_USAGE.md` (if AI tools were used)
- `requirements.txt` (or equivalent dependency file)
- Any additional files required to run the project

The README should explain:

- How to install dependencies
- How to configure the LLM (API key or Ollama)
- Which LLM provider and model were used
- How to run the application
- A brief explanation of the LangGraph workflow
- Optional: 2–3 example console sessions

## Acceptance Criteria

1. Clone the GitHub repository or extract the ZIP archive.
2. Install all required dependencies.
3. Configure either an API key or a local Ollama model.
4. Run the application from the terminal.
5. Create projects using natural language.
6. List all projects.
7. Exit the application gracefully.
8. Follow the README without requiring additional clarification.

## Evaluation Criteria

| Area | Review Focus |
| --- | --- |
| LangGraph | Correct routing and action execution |
| Functionality | Required features work correctly |
| Code Quality | Readable, modular, maintainable |
| Documentation | Clear README and AI disclosure |
| Robustness | Graceful handling of invalid or unclear input |
