"""CLI renderer — formats hub responses for terminal output."""

from neoclip.core.hub.central_hub import HubResponse


def render_response(response: HubResponse, print_fn=print):
    status = "OK" if response.success else "FAIL"
    print_fn(f"[{status}] {response.message}")
    if response.intent:
        print_fn(f"  Intent: {response.intent.value}")
    if response.needs_confirmation:
        print_fn(f"  ⚠ {response.confirmation_message}")
    if response.needs_clarification:
        print_fn(f"  ? {response.clarification}")
    if response.data:
        print_fn(f"  Data: {response.data}")
