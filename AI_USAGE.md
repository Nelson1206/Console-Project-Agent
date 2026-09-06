# AI Usage

This document shows how AI Tools use in this project.

---

## 1. Architecture discussion

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:** Asked the assignment's unspecified details before freezing specs. Confirmed answers:

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

According details, create spec 'specs/constitution.md', 'specs/spec.md', 'specs/plan.md', 'specs/tasks.md'


- **Main prompt:** 

(Plan Mode) Refer 'Take Home Assignment', discuss all detail to me. Then create spec doument.
Create spec files according to the framework:

specs/constitution.md ##Scoring principles, immutable constraints

specs/spec.md ##Intents, slots, dialogues, acceptance

specs/plan.md ##LangGraph, State, JSON schema

specs/tasks.md ##Optional implementation steps


## 2. Code Implementation

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:** Implement and test code by task
- **Main prompt:** Implement {task id from 'tasks'}


## 3. Code Optimization&Fix

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:** 
1. Add 'follow_up' to llm's intent classification set.
2. Update prompt for teach model how classify intent 'follow up'
3. change classify node to use llm classify for follow up
4. only keep update use origin classify
- **Main prompt:** when collecting classify_intent, return directly to follow_up. please use classify_with_llm to allow change intent on follow_up state.

## 4. Code Optimization&Fix 2

- **Tools:** Cursor (Grok 4.6)
- **How AI was used:** 
Change the fill_remaining logic from ‘If exactly one required field is missing, treat the whole reply as that value’ to ‘Fill the one missing required field from a bare follow-up value only.’. The change as felllow:
1. update prompts to teach model identifiy vlaue from sentence
2. add hint for filter slots

- **Main prompt:** 
currently, agenet can not identifiy the real value should extracat on fill remaining field, the following is an example:
> create a project called Alpha
I still need the customer name for this project.

> the customer is Amy
Done. Created project "Alpha" for the customer is Amy.