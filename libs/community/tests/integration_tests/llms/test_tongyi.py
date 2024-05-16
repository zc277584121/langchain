"""Test Tongyi API wrapper."""

from langchain_core.outputs import LLMResult

from langchain_community.llms.tongyi import Tongyi


def test_tongyi_call() -> None:
    """Test valid call to tongyi."""
    llm = Tongyi()  # type: ignore[call-arg]
    output = llm.invoke("who are you")
    assert isinstance(output, str)


def test_tongyi_generate() -> None:
    """Test valid call to tongyi."""
    llm = Tongyi()  # type: ignore[call-arg]
    output = llm.generate(["who are you"])
    assert isinstance(output, LLMResult)
    assert isinstance(output.generations, list)


def test_tongyi_generate_stream() -> None:
    """Test valid call to tongyi."""
    llm = Tongyi(streaming=True)  # type: ignore[call-arg]
    output = llm.generate(["who are you"])
    print(output)  # noqa: T201
    assert isinstance(output, LLMResult)
    assert isinstance(output.generations, list)
