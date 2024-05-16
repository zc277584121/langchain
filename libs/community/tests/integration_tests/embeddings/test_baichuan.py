"""Test Baichuan Text Embedding."""
from langchain_community.embeddings.baichuan import BaichuanTextEmbeddings


def test_baichuan_embedding_documents() -> None:
    """Test Baichuan Text Embedding for documents."""
    documents = ["今天天气不错", "今天阳光灿烂"]
    embedding = BaichuanTextEmbeddings()  # type: ignore[call-arg]
    output = embedding.embed_documents(documents)
    assert len(output) == 2  # type: ignore[arg-type]
    assert len(output[0]) == 1024  # type: ignore[index]


def test_baichuan_embedding_query() -> None:
    """Test Baichuan Text Embedding for query."""
    document = "所有的小学生都会学过只因兔同笼问题。"
    embedding = BaichuanTextEmbeddings()  # type: ignore[call-arg]
    output = embedding.embed_query(document)
    assert len(output) == 1024  # type: ignore[arg-type]
