import unittest
from unittest.mock import patch

from backend.services import vector_service


class _FakePanic(BaseException):
    pass


class VectorServiceChromaDegradeTests(unittest.TestCase):
    def test_build_vector_service_degrades_when_persistent_client_panics(self):
        with patch(
            "backend.services.vector_service.chromadb.PersistentClient",
            side_effect=_FakePanic("simulated chroma panic"),
        ):
            service = vector_service._build_vector_service()

        self.assertIsNone(service._client)
        self.assertIsNone(service.collection)
        self.assertEqual(service.persist_directory, vector_service.CHROMA_PATH)

    def test_delete_by_document_id_returns_false_when_persistent_client_panics(self):
        with patch(
            "backend.services.vector_service.chromadb.PersistentClient",
            side_effect=_FakePanic("simulated chroma panic"),
        ):
            result = vector_service.delete_by_document_id(123)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
