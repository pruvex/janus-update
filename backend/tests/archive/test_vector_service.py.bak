from pathlib import Path
from unittest.mock import patch


from backend.services.vector_service import VectorService


def test_vector_service_initializes_and_stores_embeddings(tmp_path: Path):
    persist_dir = tmp_path / "chroma"
    service = VectorService(str(persist_dir))

    assert service.embedding_fn is not None, "Embedding function should be built during init"
    assert service.collection is not None, "Collection must be ready after init"

    service.collection.add(
        ids=["test-doc"],
        documents=["Dies ist ein Testtext für Embeddings."],
        metadatas=[{"source": "unit-test"}],
    )

    query_result = service.collection.query(
        query_texts=["Dies ist ein Testtext für Embeddings."],
        n_results=1,
    )

    assert query_result
    assert query_result.get("ids")
    assert query_result["ids"][0][0] == "test-doc"

    try:
        service._client.delete_collection("janus_global_documents")
    except Exception:
        pass


def test_vector_service_initializes_without_embedding_function_when_builder_fails(tmp_path: Path):
    persist_dir = tmp_path / "chroma-offline"

    with patch.object(VectorService, "_build_embedding_function", return_value=None):
        service = VectorService(str(persist_dir))

    assert service.embedding_fn is None
    assert service.collection is not None, "Collection should still be created for offline degrade startup"

    try:
        service._client.delete_collection("janus_global_documents")
    except Exception:
        pass
