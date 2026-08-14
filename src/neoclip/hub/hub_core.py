"""Bridge module — re-exports CentralHub for backward compatibility.

Existing code imports:
    from neoclip.hub.hub_core import get_hub
"""

from neoclip.core.hub.central_hub import get_hub, CentralHub, HubRequest, HubResponse

__all__ = ["get_hub", "CentralHub", "HubRequest", "HubResponse"]
