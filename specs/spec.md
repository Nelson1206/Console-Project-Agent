# Specification

Behaviour spec. Implementation and acceptance follow this file. Project decisions are in `constitution.md` section 0.

## 1. Product statement

A standalone console app: an Ollama LLM understands **English** natural language, LangGraph classifies intents and runs actions, and the project list is persisted as JSON.

Users do not need to memorize command syntax. Replies are always English.

## 2. User stories

### US-1 Create a project

Create a project in one natural-language sentence. The system extracts name and customer (plus optional fields present in the sentence) and saves the record.

### US-2 Fill missing fields

If name or customer is omitted on create, the system lists all missing fields in one follow-up and keeps asking until both are present. Only then may it save.

### US-3 List projects

List all projects. If there are none, say so clearly.

### US-4 Get / update / delete

Look up a project by name to show, change, or delete it. If several share the name, disambiguate first. Never silently act on the first match.

### US-5 Stay in conversation and exit

Accept commands continuously until `quit` or `exit`, then exit cleanly.

### US-6 Unclear input

Unintelligible sentences must not crash the app. Reply in English with what the user can do.

## 3. Intent contracts

| ID | Intent | Typical trigger | Required slots | Success | Failure / follow-up |
| --- | --- | --- | --- | --- | --- |
| I-CREATE | `create` | `create a project called Alpha for customer Acme` | `project_name`, `customer` | Write JSON; golden-path reply is verbatim | List all missing fields; do not save |
| I-LIST | `list` | `list projects` | none | Readable list of all projects | Empty list: say so clearly |
| I-GET | `get` | `show project Alpha` / `get Alpha` | Resolvable target (name, or a number after disambiguation) | Show the full record | Not found, or collision → disambiguate |
| I-UPDATE | `update` | `update Alpha customer to Globex` | Target + at least one field to change | Write JSON and say what changed | Missing target or missing changes → follow-up; collision → disambiguate |
| I-DELETE | `delete` | `delete Alpha` / `remove project Beta` | Resolvable target | Delete and write JSON, **no confirmation** | Not found, or collision → disambiguate |
| I-EXIT | `exit` | `quit`, `exit` | none | End the REPL | — |
| I-UNKNOWN | `unknown` | Unclassifiable sentence | none | Explain in English and hint capabilities | Must not crash |

`quit` / `exit` may be handled by a rule before the graph. All other natural language must go through LangGraph classification.

### 3.1 Slots

| Slot | Required on create | Meaning | Normalization |
| --- | --- | --- | --- |
| `project_name` | yes | Project name | Strip; empty string counts as missing |
| `customer` | yes | Customer name | Strip; empty string counts as missing |
| `start_date` | no | Start date | Capture only if present; strip |
| `location` | no | Location | Capture only if present |
| `status` | no | Status | Capture only if present |
| `notes` | no | Notes | Capture only if present |

Duplicate names are allowed. `list` shows all of them. Do not reject create because of a duplicate name.

Lookup (get / update / delete) matches `project_name` **case-insensitively**.

### 3.2 Target selection and collisions

1. Extract `project_name` from the input, or accept a list number (`1`, `2`) while disambiguating.
2. Zero matches: `No project named "<name>" was found.`
3. One match: run the action on that record.
4. Several matches: enter `disambiguating`, list candidates (number, name, customer, id), and ask for a number.
5. If the user issues a new intent during disambiguation, cancel the pending action and do not write.

Disambiguation list format:

```text
Multiple projects named "Alpha" were found. Reply with a number:
1. Alpha — customer: Acme — id: <id>
2. Alpha — customer: Globex — id: <id>
```

## 4. Dialogue states

```text
idle ──(create slots complete)──► persist ──► idle
  │
  ├──(create missing slots)──► collecting ──(filled)──► persist ──► idle
  │                         │
  │                         ├──(still missing)──► collecting
  │                         └──(new intent)──► drop draft, run new intent
  │
  ├──(get/update/delete collision)──► disambiguating ──(number)──► act ──► idle
  │                                      └──(new intent)──► cancel, run new intent
  │
  ├──(update has target but no fields)──► collecting ──► idle
  ├──(list / get / update / delete success or clear failure)──► idle
  ├──(exit)──► stopped
  └──(unknown)──► clarify ──► idle
```

Rules:

- Start in `idle`.
- In `collecting`, the next turn is treated as slot-filling first. If classified as **any new intent** (`list` / `create` / `get` / `update` / `delete` / `exit` / `unknown` and clearly not an answer), **drop the draft** and run the new intent. A bare value such as `Acme` is not a new intent.
- In `disambiguating`, a valid number finishes the original action; a new intent cancels it.
- Follow-ups list all missing fields at once (ask for name and customer together when both are missing).
- After a successful write or a clear failure, clear the draft and return to `idle`.
- Delete does **not** ask `Are you sure?`.

## 5. Output contract

Replies are always English. Success lines from the assignment example must match verbatim.

### 5.1 create success (golden path, verbatim)

```text
Done. Created project "Alpha" for customer Acme.
```

Second project:

```text
Done. Created project "Beta" for customer Globex.
```

If optional fields were also captured, **keep that first sentence**. A second English line may mention optionals. Do not change the first sentence.

### 5.2 create follow-up (all missing fields at once)

Both missing:

```text
I still need the project name and the customer to create this project.
```

Customer only:

```text
I still need the customer name for this project.
```

Name only:

```text
I still need the project name for this project.
```

### 5.3 list with data (golden path, verbatim)

Two projects Alpha / Beta with no optional fields must be:

```text
Here are your projects (2):
1. Alpha — customer: Acme
2. Beta — customer: Globex
```

General form: first line `Here are your projects (N):`, then `N. <project_name> — customer: <customer>`. Optional fields may be appended on the same line or an indented next line without breaking that name/customer pattern. Order = JSON array order (creation order).

### 5.4 list empty

```text
No projects found. Create one by describing it in natural language.
```

Do not print only a blank line. Do not print only `Here are your projects (0):`.

### 5.5 get success

```text
Project "<name>" (id: <id>)
customer: <customer>
```

Optional fields or `created_at` each get a `field: value` line. Omit unset optional fields.

### 5.6 update success

```text
Done. Updated project "<name>" (id: <id>): <field> -> <new_value>
```

Multiple changes may be listed as `field -> value` pairs separated by semicolons.

If update has a target but no change payload:

```text
Which fields should I update? You can change project name, customer, start date, location, status, or notes.
```

### 5.7 delete success

```text
Done. Deleted project "<name>" for customer <customer> (id: <id>).
```

### 5.8 unknown

```text
I didn't understand that. You can create, list, show, update, or delete projects. Type quit or exit to leave.
```

### 5.9 exit

```text
Goodbye.
```

Then end the process with exit code 0.

### 5.10 Ollama / storage errors

One English line stating the cause (Ollama not running, model missing, JSON corrupt). No traceback. Do not exit the app.

## 6. Persistence

- Write JSON immediately after a successful create, update, or delete.
- Data survives restart.
- Missing file is treated as an empty list.
- Corrupt JSON: do not crash; reply with an English error; do not write this turn; do not silently overwrite with an empty file. Document this in README.
- Record fields are defined in `plan.md`: `id`, `project_name`, `customer`, `created_at`, plus optional fields when set.

## 7. General behaviour

- Read stdin until `quit` / `exit`.
- Empty line: ignore and show `> ` again.
- Ollama down, missing model, or timeout: English error, stay in the loop.
- Input must support the English in the assignment example. Non-English input must not crash. Replies stay English. Correct understanding of Chinese intents is not promised.

## 8. Acceptance scenarios

### AC-1 Golden path (verbatim)

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

Given an empty data file  
When those three lines are entered in order  
Then JSON has two records and the **reply bodies** match the text above verbatim (`> ` and blank lines may follow readline habits)

### AC-2 Missing customer follow-up

When `create a project called Alpha`  
Then do not write; reply `I still need the customer name for this project.`  
When `Acme`  
Then `Done. Created project "Alpha" for customer Acme.`

### AC-3 Both required fields missing

When `create a project`  
Then do not write; reply `I still need the project name and the customer to create this project.`

### AC-4 Empty list

When `list projects` and there is no data  
Then `No projects found. Create one by describing it in natural language.`

### AC-5 Exit

When `quit` or `exit` (including ` EXIT `)  
Then print `Goodbye.` and exit with code 0

### AC-6 Unknown input

When `asdfgh` or `what is the weather`  
Then do not exit, do not traceback, use the 5.8 text

### AC-7 Docs are self-contained

Given only the repo / ZIP  
When a reviewer follows README to install deps, install and start Ollama, pull the named model, and run  
Then they can complete AC-1, AC-4, and AC-5 without asking the author and without a cloud API key

### AC-8 Persistence

Given at least one created project  
When the app is restarted and the user runs `list projects`  
Then the earlier project is still shown

### AC-9 New intent during follow-up

Given the app is waiting for customer  
When the user enters `list projects`  
Then drop the draft, do not write a partial record, and run list

### AC-10 Optional fields if present

When `create a project called Gamma for customer Initech in London with status active`  
Then the saved record includes `location=London` and `status=active`, and the first sentence is still `Done. Created project "Gamma" for customer Initech.`

### AC-11 get

Given exactly one Alpha / Acme  
When `show project Alpha`  
Then show that record’s name, customer, and id

### AC-12 Duplicate-name disambiguation

Given two projects named Alpha  
When `delete Alpha`  
Then list both candidates and delete nothing  
When `2`  
Then delete only candidate 2

### AC-13 update

Given one Alpha / Acme  
When `update Alpha customer to Globex`  
Then that record’s `customer` is Globex in JSON, confirmed with the 5.6 sentence

### AC-14 delete

Given one Alpha / Acme  
When `delete Alpha`  
Then the record is gone from JSON, reply uses 5.7, **no confirmation**

### AC-15 Not found

When `get Zeta` and no such name exists  
Then `No project named "Zeta" was found.`

## 9. Non-goals

- User accounts, permissions, multi-tenancy
- Web API or frontend
- Relational database
- OpenRouter / cloud LLMs
- Enforcing unique project names
- Delete confirmation
- Multilingual replies
