import pytest

from backend.llm_providers.shared.base_transport import BaseTransport


def test_base_transport_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseTransport()


def test_base_transport_requires_all_contract_methods():
    class IncompleteTransport(BaseTransport):
        async def send(self, *, api_key, model, messages, tools=None, **kwargs):
            return {}

    with pytest.raises(TypeError):
        IncompleteTransport()
