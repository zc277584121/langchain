from langchain_ai21.chat.chat_adapter import (
    ChatAdapter,
    J2ChatAdapter,
    JambaChatCompletionsAdapter,
)


def create_chat_adapter(model: str) -> ChatAdapter:
    if "j2" in model:
        return J2ChatAdapter()

    if "jamba" in model:
        return JambaChatCompletionsAdapter()

    raise ValueError(f"Model {model} not supported.")
