"""Bridge module — re-exports CentralHub for backward compatibility.

Existing code imports:
    from penclip.hub.hub_core import get_hub
"""

from penclip.core.hub.central_hub import get_hub, CentralHub, HubRequest, HubResponse

__all__ = ["get_hub", "CentralHub", "HubRequest", "HubResponse"]
