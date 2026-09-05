"""Console REPL: one line in, one LangGraph turn, English reply out."""

from __future__ import annotations

from dotenv import load_dotenv

from project_agent.graph import invoke
from project_agent.replies import BANNER, GOODBYE, UNEXPECTED_ERROR, WELCOME
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


def _print_reply(text: str) -> None:
    print(text)
    print()


def _print_startup() -> None:
    print(BANNER)
    print()
    print(WELCOME)
    print()


def main() -> int:
    load_dotenv()
    _print_startup()
    carried: AgentState = {}
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print(GOODBYE)
            return 0
        except KeyboardInterrupt:
            print()
            print(GOODBYE)
            return 0
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            print(GOODBYE)
            return 0
        try:
            state = invoke({**carried, "user_input": line})
        except Exception:
            _print_reply(UNEXPECTED_ERROR)
            continue
        reply = state.get("reply")
        if reply:
            _print_reply(reply)
        if state.get("should_exit"):
            return 0
        carried = carry_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
