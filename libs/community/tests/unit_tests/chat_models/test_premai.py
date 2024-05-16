"""Test PremChat model"""

from typing import cast

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import SecretStr
from pytest import CaptureFixture

from langchain_community.chat_models import ChatPremAI
from langchain_community.chat_models.premai import _messages_to_prompt_dict


@pytest.mark.requires("premai")
def test_api_key_is_string() -> None:
    llm = ChatPremAI(premai_api_key="secret-api-key", project_id=8)  # type: ignore[call-arg]
    assert isinstance(llm.premai_api_key, SecretStr)


@pytest.mark.requires("premai")
def test_api_key_masked_when_passed_via_constructor(
    capsys: CaptureFixture,
) -> None:
    llm = ChatPremAI(premai_api_key="secret-api-key", project_id=8)  # type: ignore[call-arg]
    print(llm.premai_api_key, end="")  # noqa: T201
    captured = capsys.readouterr()

    assert captured.out == "**********"


def test_messages_to_prompt_dict_with_valid_messages() -> None:
    system_message, result = _messages_to_prompt_dict(
        [
            SystemMessage(content="System Prompt"),
            HumanMessage(content="User message #1"),
            AIMessage(content="AI message #1"),
            HumanMessage(content="User message #2"),
            AIMessage(content="AI message #2"),
        ]
    )
    expected = [
        {"role": "user", "content": "User message #1"},
        {"role": "assistant", "content": "AI message #1"},
        {"role": "user", "content": "User message #2"},
        {"role": "assistant", "content": "AI message #2"},
    ]

    assert system_message == "System Prompt"
    assert result == expected


@pytest.mark.requires("premai")
def test_premai_initialization() -> None:
    for model in [
        ChatPremAI(model="prem-ai-model", premai_api_key="xyz", project_id=8),  # type: ignore[call-arg]
        ChatPremAI(model_name="prem-ai-model", api_key="xyz", project_id=8),  # type: ignore[arg-type, call-arg]
    ]:
        assert model.model == "prem-ai-model"
        assert cast(SecretStr, model.premai_api_key).get_secret_value() == "xyz"
