import json
from typing import List, Optional
from unittest.mock import patch

import pytest

from langchain_community.vectorstores.azuresearch import AzureSearch
from tests.integration_tests.vectorstores.fake_embeddings import FakeEmbeddings

DEFAULT_VECTOR_DIMENSION = 4


class FakeEmbeddingsWithDimension(FakeEmbeddings):
    """Fake embeddings functionality for testing."""

    def __init__(self, dimension: int = DEFAULT_VECTOR_DIMENSION):
        super().__init__()
        self.dimension = dimension

    def embed_documents(self, embedding_texts: List[str]) -> List[List[float]]:
        """Return simple embeddings."""
        return [
            [float(1.0)] * (self.dimension - 1) + [float(i)]
            for i in range(len(embedding_texts))
        ]

    def embed_query(self, text: str) -> List[float]:
        """Return simple embeddings."""
        return [float(1.0)] * (self.dimension - 1) + [float(0.0)]


DEFAULT_INDEX_NAME = "langchain-index"
DEFAULT_ENDPOINT = "https://my-search-service.search.windows.net"
DEFAULT_KEY = "mykey"
DEFAULT_EMBEDDING_MODEL = FakeEmbeddingsWithDimension()


def mock_default_index(*args, **kwargs):  # type: ignore[no-untyped-def]
    from azure.search.documents.indexes.models import (
        ExhaustiveKnnAlgorithmConfiguration,
        ExhaustiveKnnParameters,
        HnswAlgorithmConfiguration,
        HnswParameters,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        VectorSearch,
        VectorSearchAlgorithmMetric,
        VectorSearchProfile,
    )

    return SearchIndex(
        name=DEFAULT_INDEX_NAME,
        fields=[
            SearchField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                hidden=False,
                searchable=False,
                filterable=True,
                sortable=False,
                facetable=False,
            ),
            SearchField(
                name="content",
                type=SearchFieldDataType.String,
                key=False,
                hidden=False,
                searchable=True,
                filterable=False,
                sortable=False,
                facetable=False,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=4,
                vector_search_profile_name="myHnswProfile",
            ),
            SearchField(
                name="metadata",
                type="Edm.String",
                key=False,
                hidden=False,
                searchable=True,
                filterable=False,
                sortable=False,
                facetable=False,
            ),
        ],
        vector_search=VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile", algorithm_configuration_name="default"
                ),
                VectorSearchProfile(
                    name="myExhaustiveKnnProfile",
                    algorithm_configuration_name="default_exhaustive_knn",
                ),
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="default",
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric=VectorSearchAlgorithmMetric.COSINE,
                    ),
                ),
                ExhaustiveKnnAlgorithmConfiguration(
                    name="default_exhaustive_knn",
                    parameters=ExhaustiveKnnParameters(
                        metric=VectorSearchAlgorithmMetric.COSINE
                    ),
                ),
            ],
        ),
    )


def create_vector_store() -> AzureSearch:
    return AzureSearch(
        azure_search_endpoint=DEFAULT_ENDPOINT,
        azure_search_key=DEFAULT_KEY,
        index_name=DEFAULT_INDEX_NAME,
        embedding_function=DEFAULT_EMBEDDING_MODEL,
    )


@pytest.mark.requires("azure.search.documents")
def test_init_existing_index() -> None:
    from azure.search.documents.indexes import SearchIndexClient

    def mock_create_index() -> None:
        pytest.fail("Should not create index in this test")

    with patch.multiple(
        SearchIndexClient, get_index=mock_default_index, create_index=mock_create_index
    ):
        vector_store = create_vector_store()
        assert vector_store.client is not None


@pytest.mark.requires("azure.search.documents")
def test_init_new_index() -> None:
    from azure.core.exceptions import ResourceNotFoundError
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import SearchIndex

    def no_index(self, name: str):  # type: ignore[no-untyped-def]
        raise ResourceNotFoundError

    created_index: Optional[SearchIndex] = None

    def mock_create_index(self, index):  # type: ignore[no-untyped-def]
        nonlocal created_index
        created_index = index

    with patch.multiple(
        SearchIndexClient, get_index=no_index, create_index=mock_create_index
    ):
        vector_store = create_vector_store()
        assert vector_store.client is not None
        assert created_index is not None
        assert json.dumps(created_index.as_dict()) == json.dumps(
            mock_default_index().as_dict()
        )
