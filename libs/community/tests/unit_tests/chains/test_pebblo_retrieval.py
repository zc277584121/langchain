"""
Unit tests for the PebbloRetrievalQA chain
"""

from typing import List
from unittest.mock import Mock

import pytest
from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever

from langchain_community.chains import PebbloRetrievalQA
from langchain_community.chains.pebblo_retrieval.models import (
    AuthContext,
    ChainInput,
    SemanticContext,
)
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.vectorstores.pinecone import Pinecone
from tests.unit_tests.llms.fake_llm import FakeLLM


class FakeRetriever(VectorStoreRetriever):
    """
    Test util that parrots the query back as documents
    """

    vectorstore: VectorStore = Mock()

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        return [Document(page_content=query)]

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> List[Document]:
        return [Document(page_content=query)]


@pytest.fixture
def unsupported_retriever() -> FakeRetriever:
    """
    Create a FakeRetriever instance
    """
    retriever = FakeRetriever()
    retriever.search_kwargs = {}
    # Set the class of vectorstore to Chroma
    retriever.vectorstore.__class__ = Chroma
    return retriever


@pytest.fixture
def retriever() -> FakeRetriever:
    """
    Create a FakeRetriever instance
    """
    retriever = FakeRetriever()
    retriever.search_kwargs = {}
    # Set the class of vectorstore to Pinecone
    retriever.vectorstore.__class__ = Pinecone
    return retriever


@pytest.fixture
def pebblo_retrieval_qa(retriever: FakeRetriever) -> PebbloRetrievalQA:
    """
    Create a PebbloRetrievalQA instance
    """
    pebblo_retrieval_qa = PebbloRetrievalQA.from_chain_type(
        llm=FakeLLM(), chain_type="stuff", retriever=retriever
    )

    return pebblo_retrieval_qa


def test_invoke(pebblo_retrieval_qa: PebbloRetrievalQA) -> None:
    """
    Test that the invoke method returns a non-None result
    """
    # Create a fake auth context and semantic context
    auth_context = AuthContext(
        user_id="fake_user@email.com",
        user_auth=["fake-group", "fake-group2"],
    )
    semantic_context_dict = {
        "pebblo_semantic_topics": {"deny": ["harmful-advice"]},
        "pebblo_semantic_entities": {"deny": ["credit-card"]},
    }
    semantic_context = SemanticContext(**semantic_context_dict)

    question = "What is the meaning of life?"

    chain_input_obj = ChainInput(
        query=question, auth_context=auth_context, semantic_context=semantic_context
    )
    response = pebblo_retrieval_qa.invoke(chain_input_obj.dict())
    assert response is not None


def test_validate_vectorstore(
    retriever: FakeRetriever, unsupported_retriever: FakeRetriever
) -> None:
    """
    Test vectorstore validation
    """

    # No exception should be raised for supported vectorstores (Pinecone)
    _ = PebbloRetrievalQA.from_chain_type(
        llm=FakeLLM(),
        chain_type="stuff",
        retriever=retriever,
    )

    # validate_vectorstore method should raise a ValueError for unsupported vectorstores
    with pytest.raises(ValueError) as exc_info:
        _ = PebbloRetrievalQA.from_chain_type(
            llm=FakeLLM(),
            chain_type="stuff",
            retriever=unsupported_retriever,
        )
    assert (
        "Vectorstore must be an instance of one of the supported vectorstores"
        in str(exc_info.value)
    )
