"""Test ChatOpenAI chat model."""
from typing import Any, List, Optional, cast

import pytest
from langchain_core.callbacks import CallbackManager
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.outputs import (
    ChatGeneration,
    ChatResult,
    LLMResult,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

from langchain_openai import ChatOpenAI
from tests.unit_tests.fake.callbacks import FakeCallbackHandler


@pytest.mark.scheduled
def test_chat_openai() -> None:
    """Test ChatOpenAI wrapper."""
    chat = ChatOpenAI(
        temperature=0.7,
        base_url=None,
        organization=None,
        openai_proxy=None,
        timeout=10.0,
        max_retries=3,
        http_client=None,
        n=1,
        max_tokens=10,
        default_headers=None,
        default_query=None,
    )
    message = HumanMessage(content="Hello")
    response = chat.invoke([message])
    assert isinstance(response, BaseMessage)
    assert isinstance(response.content, str)


def test_chat_openai_model() -> None:
    """Test ChatOpenAI wrapper handles model_name."""
    chat = ChatOpenAI(model="foo")
    assert chat.model_name == "foo"
    chat = ChatOpenAI(model_name="bar")
    assert chat.model_name == "bar"


def test_chat_openai_system_message() -> None:
    """Test ChatOpenAI wrapper with system message."""
    chat = ChatOpenAI(max_tokens=10)
    system_message = SystemMessage(content="You are to chat with the user.")
    human_message = HumanMessage(content="Hello")
    response = chat.invoke([system_message, human_message])
    assert isinstance(response, BaseMessage)
    assert isinstance(response.content, str)


@pytest.mark.scheduled
def test_chat_openai_generate() -> None:
    """Test ChatOpenAI wrapper with generate."""
    chat = ChatOpenAI(max_tokens=10, n=2)
    message = HumanMessage(content="Hello")
    response = chat.generate([[message], [message]])
    assert isinstance(response, LLMResult)
    assert len(response.generations) == 2
    assert response.llm_output
    for generations in response.generations:
        assert len(generations) == 2
        for generation in generations:
            assert isinstance(generation, ChatGeneration)
            assert isinstance(generation.text, str)
            assert generation.text == generation.message.content


@pytest.mark.scheduled
def test_chat_openai_multiple_completions() -> None:
    """Test ChatOpenAI wrapper with multiple completions."""
    chat = ChatOpenAI(max_tokens=10, n=5)
    message = HumanMessage(content="Hello")
    response = chat._generate([message])
    assert isinstance(response, ChatResult)
    assert len(response.generations) == 5
    for generation in response.generations:
        assert isinstance(generation.message, BaseMessage)
        assert isinstance(generation.message.content, str)


@pytest.mark.scheduled
def test_chat_openai_streaming() -> None:
    """Test that streaming correctly invokes on_llm_new_token callback."""
    callback_handler = FakeCallbackHandler()
    callback_manager = CallbackManager([callback_handler])
    chat = ChatOpenAI(
        max_tokens=10,
        streaming=True,
        temperature=0,
        callback_manager=callback_manager,
        verbose=True,
    )
    message = HumanMessage(content="Hello")
    response = chat.invoke([message])
    assert callback_handler.llm_streams > 0
    assert isinstance(response, BaseMessage)


@pytest.mark.scheduled
def test_chat_openai_streaming_generation_info() -> None:
    """Test that generation info is preserved when streaming."""

    class _FakeCallback(FakeCallbackHandler):
        saved_things: dict = {}

        def on_llm_end(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            # Save the generation
            self.saved_things["generation"] = args[0]

    callback = _FakeCallback()
    callback_manager = CallbackManager([callback])
    chat = ChatOpenAI(
        max_tokens=2,
        temperature=0,
        callback_manager=callback_manager,
    )
    list(chat.stream("hi"))
    generation = callback.saved_things["generation"]
    # `Hello!` is two tokens, assert that that is what is returned
    assert generation.generations[0][0].text == "Hello!"


def test_chat_openai_llm_output_contains_model_name() -> None:
    """Test llm_output contains model_name."""
    chat = ChatOpenAI(max_tokens=10)
    message = HumanMessage(content="Hello")
    llm_result = chat.generate([[message]])
    assert llm_result.llm_output is not None
    assert llm_result.llm_output["model_name"] == chat.model_name


def test_chat_openai_streaming_llm_output_contains_model_name() -> None:
    """Test llm_output contains model_name."""
    chat = ChatOpenAI(max_tokens=10, streaming=True)
    message = HumanMessage(content="Hello")
    llm_result = chat.generate([[message]])
    assert llm_result.llm_output is not None
    assert llm_result.llm_output["model_name"] == chat.model_name


def test_chat_openai_invalid_streaming_params() -> None:
    """Test that streaming correctly invokes on_llm_new_token callback."""
    with pytest.raises(ValueError):
        ChatOpenAI(
            max_tokens=10,
            streaming=True,
            temperature=0,
            n=5,
        )


@pytest.mark.scheduled
async def test_async_chat_openai() -> None:
    """Test async generation."""
    chat = ChatOpenAI(max_tokens=10, n=2)
    message = HumanMessage(content="Hello")
    response = await chat.agenerate([[message], [message]])
    assert isinstance(response, LLMResult)
    assert len(response.generations) == 2
    assert response.llm_output
    for generations in response.generations:
        assert len(generations) == 2
        for generation in generations:
            assert isinstance(generation, ChatGeneration)
            assert isinstance(generation.text, str)
            assert generation.text == generation.message.content


@pytest.mark.scheduled
async def test_async_chat_openai_streaming() -> None:
    """Test that streaming correctly invokes on_llm_new_token callback."""
    callback_handler = FakeCallbackHandler()
    callback_manager = CallbackManager([callback_handler])
    chat = ChatOpenAI(
        max_tokens=10,
        streaming=True,
        temperature=0,
        callback_manager=callback_manager,
        verbose=True,
    )
    message = HumanMessage(content="Hello")
    response = await chat.agenerate([[message], [message]])
    assert callback_handler.llm_streams > 0
    assert isinstance(response, LLMResult)
    assert len(response.generations) == 2
    for generations in response.generations:
        assert len(generations) == 1
        for generation in generations:
            assert isinstance(generation, ChatGeneration)
            assert isinstance(generation.text, str)
            assert generation.text == generation.message.content


@pytest.mark.scheduled
async def test_async_chat_openai_bind_functions() -> None:
    """Test ChatOpenAI wrapper with multiple completions."""

    class Person(BaseModel):
        """Identifying information about a person."""

        name: str = Field(..., title="Name", description="The person's name")
        age: int = Field(..., title="Age", description="The person's age")
        fav_food: Optional[str] = Field(
            default=None, title="Fav Food", description="The person's favorite food"
        )

    chat = ChatOpenAI(
        max_tokens=30,
        n=1,
        streaming=True,
    ).bind_functions(functions=[Person], function_call="Person")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Use the provided Person function"),
            ("user", "{input}"),
        ]
    )

    chain = prompt | chat

    message = HumanMessage(content="Sally is 13 years old")
    response = await chain.abatch([{"input": message}])

    assert isinstance(response, list)
    assert len(response) == 1
    for generation in response:
        assert isinstance(generation, AIMessage)


def test_chat_openai_extra_kwargs() -> None:
    """Test extra kwargs to chat openai."""
    # Check that foo is saved in extra_kwargs.
    llm = ChatOpenAI(foo=3, max_tokens=10)
    assert llm.max_tokens == 10
    assert llm.model_kwargs == {"foo": 3}

    # Test that if extra_kwargs are provided, they are added to it.
    llm = ChatOpenAI(foo=3, model_kwargs={"bar": 2})
    assert llm.model_kwargs == {"foo": 3, "bar": 2}

    # Test that if provided twice it errors
    with pytest.raises(ValueError):
        ChatOpenAI(foo=3, model_kwargs={"foo": 2})

    # Test that if explicit param is specified in kwargs it errors
    with pytest.raises(ValueError):
        ChatOpenAI(model_kwargs={"temperature": 0.2})

    # Test that "model" cannot be specified in kwargs
    with pytest.raises(ValueError):
        ChatOpenAI(model_kwargs={"model": "gpt-3.5-turbo-instruct"})


@pytest.mark.scheduled
def test_openai_streaming() -> None:
    """Test streaming tokens from OpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    for token in llm.stream("I'm Pickle Rick"):
        assert isinstance(token.content, str)


@pytest.mark.scheduled
async def test_openai_astream() -> None:
    """Test streaming tokens from OpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    async for token in llm.astream("I'm Pickle Rick"):
        assert isinstance(token.content, str)


@pytest.mark.scheduled
async def test_openai_abatch() -> None:
    """Test streaming tokens from ChatOpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    result = await llm.abatch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


@pytest.mark.scheduled
async def test_openai_abatch_tags() -> None:
    """Test batch tokens from ChatOpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    result = await llm.abatch(
        ["I'm Pickle Rick", "I'm not Pickle Rick"], config={"tags": ["foo"]}
    )
    for token in result:
        assert isinstance(token.content, str)


@pytest.mark.scheduled
def test_openai_batch() -> None:
    """Test batch tokens from ChatOpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    result = llm.batch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


@pytest.mark.scheduled
async def test_openai_ainvoke() -> None:
    """Test invoke tokens from ChatOpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    result = await llm.ainvoke("I'm Pickle Rick", config={"tags": ["foo"]})
    assert isinstance(result.content, str)


@pytest.mark.scheduled
def test_openai_invoke() -> None:
    """Test invoke tokens from ChatOpenAI."""
    llm = ChatOpenAI(max_tokens=10)

    result = llm.invoke("I'm Pickle Rick", config=dict(tags=["foo"]))
    assert isinstance(result.content, str)


def test_stream() -> None:
    """Test streaming tokens from OpenAI."""
    llm = ChatOpenAI()

    full: Optional[BaseMessageChunk] = None
    for chunk in llm.stream("I'm Pickle Rick"):
        assert isinstance(chunk.content, str)
        full = chunk if full is None else full + chunk


async def test_astream() -> None:
    """Test streaming tokens from OpenAI."""
    llm = ChatOpenAI()

    full: Optional[BaseMessageChunk] = None
    async for chunk in llm.astream("I'm Pickle Rick"):
        assert isinstance(chunk.content, str)
        full = chunk if full is None else full + chunk


async def test_abatch() -> None:
    """Test streaming tokens from ChatOpenAI."""
    llm = ChatOpenAI()

    result = await llm.abatch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


async def test_abatch_tags() -> None:
    """Test batch tokens from ChatOpenAI."""
    llm = ChatOpenAI()

    result = await llm.abatch(
        ["I'm Pickle Rick", "I'm not Pickle Rick"], config={"tags": ["foo"]}
    )
    for token in result:
        assert isinstance(token.content, str)


def test_batch() -> None:
    """Test batch tokens from ChatOpenAI."""
    llm = ChatOpenAI()

    result = llm.batch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


async def test_ainvoke() -> None:
    """Test invoke tokens from ChatOpenAI."""
    llm = ChatOpenAI()

    result = await llm.ainvoke("I'm Pickle Rick", config={"tags": ["foo"]})
    assert isinstance(result.content, str)


def test_invoke() -> None:
    """Test invoke tokens from ChatOpenAI."""
    llm = ChatOpenAI()

    result = llm.invoke("I'm Pickle Rick", config=dict(tags=["foo"]))
    assert isinstance(result.content, str)


def test_response_metadata() -> None:
    llm = ChatOpenAI()
    result = llm.invoke([HumanMessage(content="I'm PickleRick")], logprobs=True)
    assert result.response_metadata
    assert all(
        k in result.response_metadata
        for k in (
            "token_usage",
            "model_name",
            "logprobs",
            "system_fingerprint",
            "finish_reason",
        )
    )
    assert "content" in result.response_metadata["logprobs"]


async def test_async_response_metadata() -> None:
    llm = ChatOpenAI()
    result = await llm.ainvoke([HumanMessage(content="I'm PickleRick")], logprobs=True)
    assert result.response_metadata
    assert all(
        k in result.response_metadata
        for k in (
            "token_usage",
            "model_name",
            "logprobs",
            "system_fingerprint",
            "finish_reason",
        )
    )
    assert "content" in result.response_metadata["logprobs"]


def test_response_metadata_streaming() -> None:
    llm = ChatOpenAI()
    full: Optional[BaseMessageChunk] = None
    for chunk in llm.stream("I'm Pickle Rick", logprobs=True):
        assert isinstance(chunk.content, str)
        full = chunk if full is None else full + chunk
    assert all(
        k in cast(BaseMessageChunk, full).response_metadata
        for k in (
            "logprobs",
            "finish_reason",
        )
    )
    assert "content" in cast(BaseMessageChunk, full).response_metadata["logprobs"]


async def test_async_response_metadata_streaming() -> None:
    llm = ChatOpenAI()
    full: Optional[BaseMessageChunk] = None
    async for chunk in llm.astream("I'm Pickle Rick", logprobs=True):
        assert isinstance(chunk.content, str)
        full = chunk if full is None else full + chunk
    assert all(
        k in cast(BaseMessageChunk, full).response_metadata
        for k in (
            "logprobs",
            "finish_reason",
        )
    )
    assert "content" in cast(BaseMessageChunk, full).response_metadata["logprobs"]


class GenerateUsername(BaseModel):
    "Get a username based on someone's name and hair color."

    name: str
    hair_color: str


class MakeASandwich(BaseModel):
    "Make a sandwich given a list of ingredients."

    bread_type: str
    cheese_type: str
    condiments: List[str]
    vegetables: List[str]


def test_tool_use() -> None:
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    llm_with_tool = llm.bind_tools(tools=[GenerateUsername], tool_choice=True)
    msgs: List = [HumanMessage("Sally has green hair, what would her username be?")]
    ai_msg = llm_with_tool.invoke(msgs)

    assert isinstance(ai_msg, AIMessage)
    assert isinstance(ai_msg.tool_calls, list)
    assert len(ai_msg.tool_calls) == 1
    tool_call = ai_msg.tool_calls[0]
    assert "args" in tool_call

    tool_msg = ToolMessage(
        "sally_green_hair", tool_call_id=ai_msg.additional_kwargs["tool_calls"][0]["id"]
    )
    msgs.extend([ai_msg, tool_msg])
    llm_with_tool.invoke(msgs)

    # Test streaming
    ai_messages = llm_with_tool.stream(msgs)
    first = True
    for message in ai_messages:
        if first:
            gathered = message
            first = False
        else:
            gathered = gathered + message  # type: ignore
    assert isinstance(gathered, AIMessageChunk)
    assert isinstance(gathered.tool_call_chunks, list)
    assert len(gathered.tool_call_chunks) == 1
    tool_call_chunk = gathered.tool_call_chunks[0]
    assert "args" in tool_call_chunk

    streaming_tool_msg = ToolMessage(
        "sally_green_hair",
        tool_call_id=gathered.additional_kwargs["tool_calls"][0]["id"],
    )
    msgs.extend([gathered, streaming_tool_msg])
    llm_with_tool.invoke(msgs)


def test_manual_tool_call_msg() -> None:
    """Test passing in manually construct tool call message."""
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    llm_with_tool = llm.bind_tools(tools=[GenerateUsername])
    msgs: List = [
        HumanMessage("Sally has green hair, what would her username be?"),
        AIMessage(
            content="",
            tool_calls=[
                ToolCall(
                    name="GenerateUsername",
                    args={"name": "Sally", "hair_color": "green"},
                    id="foo",
                )
            ],
        ),
        ToolMessage("sally_green_hair", tool_call_id="foo"),
    ]
    output: AIMessage = cast(AIMessage, llm_with_tool.invoke(msgs))
    assert output.content
    # Should not have called the tool again.
    assert not output.tool_calls and not output.invalid_tool_calls

    # OpenAI should error when tool call id doesn't match across AIMessage and
    # ToolMessage
    msgs = [
        HumanMessage("Sally has green hair, what would her username be?"),
        AIMessage(
            content="",
            tool_calls=[
                ToolCall(
                    name="GenerateUsername",
                    args={"name": "Sally", "hair_color": "green"},
                    id="bar",
                )
            ],
        ),
        ToolMessage("sally_green_hair", tool_call_id="foo"),
    ]
    with pytest.raises(Exception):
        llm_with_tool.invoke(msgs)


def test_bind_tools_tool_choice() -> None:
    """Test passing in manually construct tool call message."""
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    for tool_choice in ("any", "required"):
        llm_with_tools = llm.bind_tools(
            tools=[GenerateUsername, MakeASandwich], tool_choice=tool_choice
        )
        msg = cast(AIMessage, llm_with_tools.invoke("how are you"))
        assert msg.tool_calls

    llm_with_tools = llm.bind_tools(tools=[GenerateUsername, MakeASandwich])
    msg = cast(AIMessage, llm_with_tools.invoke("how are you"))
    assert not msg.tool_calls


def test_openai_structured_output() -> None:
    class MyModel(BaseModel):
        """A Person"""

        name: str
        age: int

    llm = ChatOpenAI().with_structured_output(MyModel)
    result = llm.invoke("I'm a 27 year old named Erick")
    assert isinstance(result, MyModel)
    assert result.name == "Erick"
    assert result.age == 27


def test_openai_proxy() -> None:
    """Test ChatOpenAI with proxy."""
    chat_openai = ChatOpenAI(
        openai_proxy="http://localhost:8080",
    )
    mounts = chat_openai.client._client._client._mounts
    assert len(mounts) == 1
    for key, value in mounts.items():
        proxy = value._pool._proxy_url.origin
        assert proxy.scheme == b"http"
        assert proxy.host == b"localhost"
        assert proxy.port == 8080

    async_client_mounts = chat_openai.async_client._client._client._mounts
    assert len(async_client_mounts) == 1
    for key, value in async_client_mounts.items():
        proxy = value._pool._proxy_url.origin
        assert proxy.scheme == b"http"
        assert proxy.host == b"localhost"
        assert proxy.port == 8080
