# AI Usage

This document describes how AI tools were used in this project.

---

## 1. Architecture discussion

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:** Asked about the assignment's unspecified details before freezing the specs. Confirmed answers:

  1. Scope — implement required create/list plus full bonus (optional fields and get/update/delete).
  2. LLM provider — Ollama only; no OpenRouter or other cloud API path.
  3. Reply language — always English.
  4. Output fidelity — golden-path create/list replies must match the assignment example verbatim.
  5. Duplicate names — allowed; list shows all of them.
  6. Target for get/update/delete — look up by `project_name`; on collision, list candidates and ask the user to specify.
  7. Optional fields on create — accept them if present in the sentence; do not prompt for missing optionals.
  8. Interrupted follow-up — any new intent cancels the unfinished draft.
  9. Missing required fields — ask for all missing fields in one follow-up.
  10. JSON record shape — required fields, optional fields when set, plus `id` and `created_at`.

From those decisions, the spec files were created: `specs/constitution.md`, `specs/spec.md`, `specs/plan.md`, `specs/tasks.md`.

- **Main prompt:**

(Plan Mode) Refer to 'Take Home Assignment', discuss all details with me. Then create spec documents.
Create spec files according to the framework:

specs/constitution.md ## Scoring principles, immutable constraints

specs/spec.md ## Intents, slots, dialogues, acceptance

specs/plan.md ## LangGraph, State, JSON schema

specs/tasks.md ## Optional implementation steps

## 2. Code implementation

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:** Implement and test code task by task.
- **Main prompt:** Implement {task id from 'tasks'}

## 3. Code optimization and fix

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:**
  1. Add `follow_up` to the LLM intent classification set.
  2. Update the classify prompt so the model can choose `follow_up` when the user is answering a pending question.
  3. Change the classify node so collecting turns call `classify_with_llm` instead of always returning `follow_up`.
  4. Keep a hard guard for update collection: if the model returns `update` while a target is already locked, treat it as `follow_up` so the selected project is not cleared.
- **Main prompt:** When collecting, `classify_intent` currently returns `follow_up` directly. Please use `classify_with_llm` so the user can change intent during a follow-up.

## 4. Code optimization and fix 2

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:**
  Change `fill_remaining` from “if exactly one required field is missing, treat the whole reply as that value” to “fill the one missing required field from a bare follow-up value only.” The changes were:
  1. Update extract prompts so the model takes the value out of a labeled sentence.
  2. Add filters so commands, labeled clauses, and questions are not written into a slot whole.
- **Main prompt:**
  Currently the agent cannot identify the real value to extract when filling a remaining field. Example:

  > create a project called Alpha
  I still need the customer name for this project.

  > the customer is Amy
  Done. Created project "Alpha" for the customer is Amy.

## 5. Code optimization and fix 3

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:**
  The model treated `Acme` as a project name, so the intent was marked `get`. Change: while `dialog_state` is `collecting`, any input that looks like a bare value is forced to `follow_up`, even if the model first marks it as `get`, `delete`, or `unknown`.
- **Main prompt:**
  The LLM does not correctly identify the intent in this case:

  > create a project called Alpha
  I still need the customer name for this project.

  > Acme
  No project named "Acme" was found.
