"""CLI renderer — formats hub responses for terminal output."""

from neoclip.core.hub.central_hub import HubResponse


def render_response(response: HubResponse):
    status = "OK" if response.success else "FAIL"
    print(f"[{status}] {response.message}")
    if response.intent:
        print(f"  Intent: {response.intent.value}")
    if response.needs_confirmation:
        print(f"  ⚠ {response.confirmation_message}")
    if response.data:
        print(f"  Data: {response.data}")
