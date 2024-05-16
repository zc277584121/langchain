"""Test Chroma functionality."""

import uuid
from typing import Generator

import chromadb
import pytest
import requests
from chromadb.api.client import SharedSystemClient
from langchain_core.documents import Document
from langchain_core.embeddings.fake import FakeEmbeddings as Fak

from langchain_chroma.vectorstores import Chroma
from tests.integration_tests.fake_embeddings import (
    ConsistentFakeEmbeddings,
    FakeEmbeddings,
)


@pytest.fixture()
def client() -> Generator[chromadb.ClientAPI, None, None]:
    SharedSystemClient.clear_system_cache()
    client = chromadb.Client(chromadb.config.Settings())
    yield client


def test_chroma() -> None:
    """Test end to end construction and search."""
    texts = ["foo", "bar", "baz"]
    docsearch = Chroma.from_texts(
        collection_name="test_collection", texts=texts, embedding=FakeEmbeddings()
    )
    output = docsearch.similarity_search("foo", k=1)

    docsearch.delete_collection()

    assert output == [Document(page_content="foo")]


async def test_chroma_async() -> None:
    """Test end to end construction and search."""
    texts = ["foo", "bar", "baz"]
    docsearch = Chroma.from_texts(
        collection_name="test_collection", texts=texts, embedding=FakeEmbeddings()
    )
    output = await docsearch.asimilarity_search("foo", k=1)

    docsearch.delete_collection()
    assert output == [Document(page_content="foo")]


def test_chroma_with_metadatas() -> None:
    """Test end to end construction and search."""
    texts = ["foo", "bar", "baz"]
    metadatas = [{"page": str(i)} for i in range(len(texts))]
    docsearch = Chroma.from_texts(
        collection_name="test_collection",
        texts=texts,
        embedding=FakeEmbeddings(),
        metadatas=metadatas,
    )
    output = docsearch.similarity_search("foo", k=1)
    docsearch.delete_collection()
    assert output == [Document(page_content="foo", metadata={"page": "0"})]


def test_chroma_with_metadatas_with_scores() -> None:
    """Test end to end construction and scored search."""
    texts = ["foo", "bar", "baz"]
    metadatas = [{"page": str(i)} for i in range(len(texts))]
    docsearch = Chroma.from_texts(
        collection_name="test_collection",
        texts=texts,
        embedding=FakeEmbeddings(),
        metadatas=metadatas,
    )
    output = docsearch.similarity_search_with_score("foo", k=1)
    docsearch.delete_collection()
    assert output == [(Document(page_content="foo", metadata={"page": "0"}), 0.0)]


def test_chroma_with_metadatas_with_scores_using_vector() -> None:
    """Test end to end construction and scored search, using embedding vector."""
    texts = ["foo", "bar", "baz"]
    metadatas = [{"page": str(i)} for i in range(len(texts))]
    embeddings = FakeEmbeddings()

    docsearch = Chroma.from_texts(
        collection_name="test_collection",
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
    )
    embedded_query = embeddings.embed_query("foo")
    output = docsearch.similarity_search_by_vector_with_relevance_scores(
        embedding=embedded_query, k=1
    )
    docsearch.delete_collection()
    assert output == [(Document(page_content="foo", metadata={"page": "0"}), 0.0)]


def test_chroma_search_filter() -> None:
    """Test end to end construction and search with metadata filtering."""
    texts = ["far", "bar", "baz"]
    metadatas = [{"first_letter": "{}".format(text[0])} for text in texts]
    docsearch = Chroma.from_texts(
        collection_name="test_collection",
        texts=texts,
        embedding=FakeEmbeddings(),
        metadatas=metadatas,
    )
    output1 = docsearch.similarity_search("far", k=1, filter={"first_letter": "f"})
    output2 = docsearch.similarity_search("far", k=1, filter={"first_letter": "b"})
    docsearch.delete_collection()
    assert output1 == [Document(page_content="far", metadata={"first_letter": "f"})]
    assert output2 == [Document(page_content="bar", metadata={"first_letter": "b"})]


def test_chroma_search_filter_with_scores() -> None:
    """Test end to end construction and scored search with metadata filtering."""
    texts = ["far", "bar", "baz"]
    metadatas = [{"first_letter": "{}".format(text[0])} for text in texts]
    docsearch = Chroma.from_texts(
        collection_name="test_collection",
        texts=texts,
        embedding=FakeEmbeddings(),
        metadatas=metadatas,
    )
    output1 = docsearch.similarity_search_with_score(
        "far", k=1, filter={"first_letter": "f"}
    )
    output2 = docsearch.similarity_search_with_score(
        "far", k=1, filter={"first_letter": "b"}
    )
    docsearch.delete_collection()
    assert output1 == [
        (Document(page_content="far", metadata={"first_letter": "f"}), 0.0)
    ]
    assert output2 == [
        (Document(page_content="bar", metadata={"first_letter": "b"}), 1.0)
    ]


def test_chroma_with_persistence() -> None:
    """Test end to end construction and search, with persistence."""
    chroma_persist_dir = "./tests/persist_dir"
    collection_name = "test_collection"
    texts = ["foo", "bar", "baz"]
    docsearch = Chroma.from_texts(
        collection_name=collection_name,
        texts=texts,
        embedding=FakeEmbeddings(),
        persist_directory=chroma_persist_dir,
    )

    output = docsearch.similarity_search("foo", k=1)
    assert output == [Document(page_content="foo")]

    # Get a new VectorStore from the persisted directory
    docsearch = Chroma(
        collection_name=collection_name,
        embedding_function=FakeEmbeddings(),
        persist_directory=chroma_persist_dir,
    )
    output = docsearch.similarity_search("foo", k=1)

    # Clean up
    docsearch.delete_collection()

    # Persist doesn't need to be called again
    # Data will be automatically persisted on object deletion
    # Or on program exit


def test_chroma_mmr() -> None:
    """Test end to end construction and search."""
    texts = ["foo", "bar", "baz"]
    docsearch = Chroma.from_texts(
        collection_name="test_collection", texts=texts, embedding=FakeEmbeddings()
    )
    output = docsearch.max_marginal_relevance_search("foo", k=1)
    docsearch.delete_collection()
    assert output == [Document(page_content="foo")]


def test_chroma_mmr_by_vector() -> None:
    """Test end to end construction and search."""
    texts = ["foo", "bar", "baz"]
    embeddings = FakeEmbeddings()
    docsearch = Chroma.from_texts(
        collection_name="test_collection", texts=texts, embedding=embeddings
    )
    embedded_query = embeddings.embed_query("foo")
    output = docsearch.max_marginal_relevance_search_by_vector(embedded_query, k=1)
    docsearch.delete_collection()
    assert output == [Document(page_content="foo")]


def test_chroma_with_include_parameter() -> None:
    """Test end to end construction and include parameter."""
    texts = ["foo", "bar", "baz"]
    docsearch = Chroma.from_texts(
        collection_name="test_collection", texts=texts, embedding=FakeEmbeddings()
    )
    output1 = docsearch.get(include=["embeddings"])
    output2 = docsearch.get()
    docsearch.delete_collection()
    assert output1["embeddings"] is not None
    assert output2["embeddings"] is None


def test_chroma_update_document() -> None:
    """Test the update_document function in the Chroma class."""
    # Make a consistent embedding
    embedding = ConsistentFakeEmbeddings()

    # Initial document content and id
    initial_content = "foo"
    document_id = "doc1"

    # Create an instance of Document with initial content and metadata
    original_doc = Document(page_content=initial_content, metadata={"page": "0"})

    # Initialize a Chroma instance with the original document
    docsearch = Chroma.from_documents(
        collection_name="test_collection",
        documents=[original_doc],
        embedding=embedding,
        ids=[document_id],
    )
    old_embedding = docsearch._collection.peek()["embeddings"][  # type: ignore
        docsearch._collection.peek()["ids"].index(document_id)
    ]

    # Define updated content for the document
    updated_content = "updated foo"

    # Create a new Document instance with the updated content and the same id
    updated_doc = Document(page_content=updated_content, metadata={"page": "0"})

    # Update the document in the Chroma instance
    docsearch.update_document(document_id=document_id, document=updated_doc)

    # Perform a similarity search with the updated content
    output = docsearch.similarity_search(updated_content, k=1)

    # Assert that the new embedding is correct
    new_embedding = docsearch._collection.peek()["embeddings"][  # type: ignore
        docsearch._collection.peek()["ids"].index(document_id)
    ]

    docsearch.delete_collection()

    # Assert that the updated document is returned by the search
    assert output == [Document(page_content=updated_content, metadata={"page": "0"})]

    assert new_embedding == embedding.embed_documents([updated_content])[0]
    assert new_embedding != old_embedding


# TODO: RELEVANCE SCORE IS BROKEN. FIX TEST
def test_chroma_with_relevance_score_custom_normalization_fn() -> None:
    """Test searching with relevance score and custom normalization function."""
    texts = ["foo", "bar", "baz"]
    metadatas = [{"page": str(i)} for i in range(len(texts))]
    docsearch = Chroma.from_texts(
        collection_name="test1_collection",
        texts=texts,
        embedding=FakeEmbeddings(),
        metadatas=metadatas,
        relevance_score_fn=lambda d: d * 0,
        collection_metadata={"hnsw:space": "l2"},
    )
    output = docsearch.similarity_search_with_relevance_scores("foo", k=3)
    docsearch.delete_collection()
    assert output == [
        (Document(page_content="foo", metadata={"page": "0"}), 0.0),
        (Document(page_content="bar", metadata={"page": "1"}), 0.0),
        (Document(page_content="baz", metadata={"page": "2"}), 0.0),
    ]


def test_init_from_client(client: chromadb.ClientAPI) -> None:
    Chroma(client=client)


def test_init_from_client_settings() -> None:
    import chromadb

    client_settings = chromadb.config.Settings()
    Chroma(client_settings=client_settings)


def test_chroma_add_documents_no_metadata() -> None:
    db = Chroma(embedding_function=FakeEmbeddings())
    db.add_documents([Document(page_content="foo")])

    db.delete_collection()


def test_chroma_add_documents_mixed_metadata() -> None:
    db = Chroma(embedding_function=FakeEmbeddings())
    docs = [
        Document(page_content="foo"),
        Document(page_content="bar", metadata={"baz": 1}),
    ]
    ids = ["0", "1"]
    actual_ids = db.add_documents(docs, ids=ids)
    search = db.similarity_search("foo bar")
    db.delete_collection()

    assert actual_ids == ids
    assert sorted(search, key=lambda d: d.page_content) == sorted(
        docs, key=lambda d: d.page_content
    )


def is_api_accessible(url: str) -> bool:
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception:
        return False


def batch_support_chroma_version() -> bool:
    major, minor, patch = chromadb.__version__.split(".")
    if int(major) == 0 and int(minor) >= 4 and int(patch) >= 10:
        return True
    return False


@pytest.mark.requires("chromadb")
@pytest.mark.skipif(
    not is_api_accessible("http://localhost:8000/api/v1/heartbeat"),
    reason="API not accessible",
)
@pytest.mark.skipif(
    not batch_support_chroma_version(),
    reason="ChromaDB version does not support batching",
)
def test_chroma_large_batch() -> None:
    client = chromadb.HttpClient()
    embedding_function = Fak(size=255)
    col = client.get_or_create_collection(
        "my_collection",
        embedding_function=embedding_function.embed_documents,  # type: ignore
    )
    docs = ["This is a test document"] * (client.max_batch_size + 100)
    db = Chroma.from_texts(
        client=client,
        collection_name=col.name,
        texts=docs,
        embedding=embedding_function,
        ids=[str(uuid.uuid4()) for _ in range(len(docs))],
    )

    db.delete_collection()


@pytest.mark.requires("chromadb")
@pytest.mark.skipif(
    not is_api_accessible("http://localhost:8000/api/v1/heartbeat"),
    reason="API not accessible",
)
@pytest.mark.skipif(
    not batch_support_chroma_version(),
    reason="ChromaDB version does not support batching",
)
def test_chroma_large_batch_update() -> None:
    client = chromadb.HttpClient()
    embedding_function = Fak(size=255)
    col = client.get_or_create_collection(
        "my_collection",
        embedding_function=embedding_function.embed_documents,  # type: ignore
    )
    docs = ["This is a test document"] * (client.max_batch_size + 100)
    ids = [str(uuid.uuid4()) for _ in range(len(docs))]
    db = Chroma.from_texts(
        client=client,
        collection_name=col.name,
        texts=docs,
        embedding=embedding_function,
        ids=ids,
    )
    new_docs = [
        Document(
            page_content="This is a new test document", metadata={"doc_id": f"{i}"}
        )
        for i in range(len(docs) - 10)
    ]
    new_ids = [_id for _id in ids[: len(new_docs)]]
    db.update_documents(ids=new_ids, documents=new_docs)

    db.delete_collection()


@pytest.mark.requires("chromadb")
@pytest.mark.skipif(
    not is_api_accessible("http://localhost:8000/api/v1/heartbeat"),
    reason="API not accessible",
)
@pytest.mark.skipif(
    batch_support_chroma_version(), reason="ChromaDB version does not support batching"
)
def test_chroma_legacy_batching() -> None:
    client = chromadb.HttpClient()
    embedding_function = Fak(size=255)
    col = client.get_or_create_collection(
        "my_collection",
        embedding_function=embedding_function.embed_documents,  # type: ignore
    )
    docs = ["This is a test document"] * 100
    db = Chroma.from_texts(
        client=client,
        collection_name=col.name,
        texts=docs,
        embedding=embedding_function,
        ids=[str(uuid.uuid4()) for _ in range(len(docs))],
    )

    db.delete_collection()


def test_create_collection_if_not_exist_default() -> None:
    """Tests existing behaviour without the new create_collection_if_not_exists flag."""
    texts = ["foo", "bar", "baz"]
    docsearch = Chroma.from_texts(
        collection_name="test_collection", texts=texts, embedding=FakeEmbeddings()
    )
    assert docsearch._client.get_collection("test_collection") is not None
    docsearch.delete_collection()


def test_create_collection_if_not_exist_true_existing(
    client: chromadb.ClientAPI,
) -> None:
    """Tests create_collection_if_not_exists=True and collection already existing."""
    client.create_collection("test_collection")
    vectorstore = Chroma(
        client=client,
        collection_name="test_collection",
        embedding_function=FakeEmbeddings(),
        create_collection_if_not_exists=True,
    )
    assert vectorstore._client.get_collection("test_collection") is not None
    vectorstore.delete_collection()


def test_create_collection_if_not_exist_false_existing(
    client: chromadb.ClientAPI,
) -> None:
    """Tests create_collection_if_not_exists=False and collection already existing."""
    client.create_collection("test_collection")
    vectorstore = Chroma(
        client=client,
        collection_name="test_collection",
        embedding_function=FakeEmbeddings(),
        create_collection_if_not_exists=False,
    )
    assert vectorstore._client.get_collection("test_collection") is not None
    vectorstore.delete_collection()


def test_create_collection_if_not_exist_false_non_existing(
    client: chromadb.ClientAPI,
) -> None:
    """Tests create_collection_if_not_exists=False and collection not-existing,
    should raise."""
    with pytest.raises(Exception, match="does not exist"):
        Chroma(
            client=client,
            collection_name="test_collection",
            embedding_function=FakeEmbeddings(),
            create_collection_if_not_exists=False,
        )


def test_create_collection_if_not_exist_true_non_existing(
    client: chromadb.ClientAPI,
) -> None:
    """Tests create_collection_if_not_exists=True and collection non-existing. ."""
    vectorstore = Chroma(
        client=client,
        collection_name="test_collection",
        embedding_function=FakeEmbeddings(),
        create_collection_if_not_exists=True,
    )

    assert vectorstore._client.get_collection("test_collection") is not None
    vectorstore.delete_collection()
