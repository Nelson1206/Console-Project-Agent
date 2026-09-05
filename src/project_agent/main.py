"""Console REPL: one line in, one LangGraph turn, English reply out."""

from __future__ import annotations

from dotenv import load_dotenv

from project_agent.graph import invoke
from project_agent.replies import GOODBYE
from project_agent.state import AgentState

CARRY_FIELDS = (
    "dialog_state",
    "draft",
    "updates",
    "pending_action",
    "pending_matches",
    "selected_id",
    "lookup_name",
    "missing_fields",
)


def carry_state(state: AgentState) -> AgentState:
    return {key: state[key] for key in CARRY_FIELDS if key in state}


def main() -> int:
    load_dotenv()
    carried: AgentState = {}
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print(GOODBYE)
            return 0
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            print(GOODBYE)
            return 0
        state = invoke({**carried, "user_input": line})
        reply = state.get("reply")
        if reply:
            print(reply)
        if state.get("should_exit"):
            return 0
        carried = carry_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
