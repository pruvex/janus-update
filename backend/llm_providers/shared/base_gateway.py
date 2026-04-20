from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProviderGateway(ABC):
    """Abstrakte Basis für alle Provider-Gateways im Janus-Silo."""

    @staticmethod
    def _gateway_helpers():
        from backend.services import llm_gateway as gateway_helpers

        return gateway_helpers

    @abstractmethod
    async def reason_and_respond(self, **kwargs) -> Dict[str, Any]:
        """Die Haupt-Orchestrierungsschleife des Providers."""
        raise NotImplementedError
