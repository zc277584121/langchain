import asyncio
from functools import partial
from typing import Any, Dict, List, Mapping, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.pydantic_v1 import root_validator

from langchain_ai21.ai21_base import AI21Base
from langchain_ai21.chat.chat_adapter import ChatAdapter
from langchain_ai21.chat.chat_factory import create_chat_adapter


class ChatAI21(BaseChatModel, AI21Base):
    """ChatAI21 chat model.

    Example:
        .. code-block:: python

            from langchain_ai21 import ChatAI21


            model = ChatAI21()
    """

    model: str
    """Model type you wish to interact with. 
        You can view the options at https://github.com/AI21Labs/ai21-python?tab=readme-ov-file#model-types"""
    num_results: int = 1
    """The number of responses to generate for a given prompt."""

    max_tokens: int = 16
    """The maximum number of tokens to generate for each response."""

    min_tokens: int = 0
    """The minimum number of tokens to generate for each response."""

    temperature: float = 0.7
    """A value controlling the "creativity" of the model's responses."""

    top_p: float = 1
    """A value controlling the diversity of the model's responses."""

    top_k_return: int = 0
    """The number of top-scoring tokens to consider for each generation step."""

    frequency_penalty: Optional[Any] = None
    """A penalty applied to tokens that are frequently generated."""

    presence_penalty: Optional[Any] = None
    """ A penalty applied to tokens that are already present in the prompt."""

    count_penalty: Optional[Any] = None
    """A penalty applied to tokens based on their frequency 
    in the generated responses."""

    n: int = 1
    """Number of chat completions to generate for each prompt."""

    _chat_adapter: ChatAdapter

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        values = super().validate_environment(values)
        model = values.get("model")

        values["_chat_adapter"] = create_chat_adapter(model)  # type: ignore

        return values

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "chat-ai21"

    @property
    def _default_params(self) -> Mapping[str, Any]:
        base_params = {
            "model": self.model,
            "num_results": self.num_results,
            "max_tokens": self.max_tokens,
            "min_tokens": self.min_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k_return": self.top_k_return,
            "n": self.n,
        }

        if self.count_penalty is not None:
            base_params["count_penalty"] = self.count_penalty.to_dict()

        if self.frequency_penalty is not None:
            base_params["frequency_penalty"] = self.frequency_penalty.to_dict()

        if self.presence_penalty is not None:
            base_params["presence_penalty"] = self.presence_penalty.to_dict()

        return base_params

    def _build_params_for_request(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Mapping[str, Any]:
        params = {}
        converted_messages = self._chat_adapter.convert_messages(messages)

        if stop is not None:
            if "stop" in kwargs:
                raise ValueError("stop is defined in both stop and kwargs")
            params["stop_sequences"] = stop

        return {
            **converted_messages,
            **self._default_params,
            **params,
            **kwargs,
        }

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        params = self._build_params_for_request(messages=messages, stop=stop, **kwargs)
        messages = self._chat_adapter.call(self.client, **params)
        generations = [ChatGeneration(message=message) for message in messages]

        return ChatResult(generations=generations)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return await asyncio.get_running_loop().run_in_executor(
            None, partial(self._generate, **kwargs), messages, stop, run_manager
        )

    def _get_system_message_from_message(self, message: BaseMessage) -> str:
        if not isinstance(message.content, str):
            raise ValueError(
                f"System Message must be of type str. Got {type(message.content)}"
            )

        return message.content
