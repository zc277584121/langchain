import logging
import os
import warnings
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import openai
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import (
    BaseModel,
    Extra,
    Field,
    SecretStr,
    root_validator,
)
from langchain_core.utils import (
    convert_to_secret_str,
    get_from_dict_or_env,
    get_pydantic_field_names,
)

logger = logging.getLogger(__name__)

DEFAULT_EMBED_BATCH_SIZE = 10
MAX_EMBED_BATCH_SIZE = 100


class UpstageEmbeddings(BaseModel, Embeddings):
    """UpstageEmbeddings embedding model.

    To use, set the environment variable `UPSTAGE_API_KEY` with your API key or
    pass it as a named parameter to the constructor.

    Example:
        .. code-block:: python

            from langchain_upstage import UpstageEmbeddings

            model = UpstageEmbeddings()
    """

    client: Any = Field(default=None, exclude=True)  #: :meta private:
    async_client: Any = Field(default=None, exclude=True)  #: :meta private:
    model: str = Field(...)
    """Embeddings model name to use. Do not add suffixes like `-query` and `-passage`.
    Instead, use 'solar-embedding-1-large' for example.
    """
    dimensions: Optional[int] = None
    """The number of dimensions the resulting output embeddings should have.
    
    Not yet supported. 
    """
    upstage_api_key: Optional[SecretStr] = Field(default=None, alias="api_key")
    """API Key for Solar API."""
    upstage_api_base: str = Field(
        default="https://api.upstage.ai/v1/solar", alias="base_url"
    )
    """Endpoint URL to use."""
    embedding_ctx_length: int = 4096
    """The maximum number of tokens to embed at once.
    
    Not yet supported.
    """
    embed_batch_size: int = DEFAULT_EMBED_BATCH_SIZE
    allowed_special: Union[Literal["all"], Set[str]] = set()
    """Not yet supported."""
    disallowed_special: Union[Literal["all"], Set[str], Sequence[str]] = "all"
    """Not yet supported."""
    chunk_size: int = 1000
    """Maximum number of texts to embed in each batch.
    
    Not yet supported.
    """
    max_retries: int = 2
    """Maximum number of retries to make when generating."""
    request_timeout: Optional[Union[float, Tuple[float, float], Any]] = Field(
        default=None, alias="timeout"
    )
    """Timeout for requests to Upstage embedding API. Can be float, httpx.Timeout or
        None."""
    show_progress_bar: bool = False
    """Whether to show a progress bar when embedding.
    
    Not yet supported.
    """
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """Holds any model parameters valid for `create` call not explicitly specified."""
    skip_empty: bool = False
    """Whether to skip empty strings when embedding or raise an error.
    Defaults to not skipping.
    
    Not yet supported."""
    default_headers: Union[Mapping[str, str], None] = None
    default_query: Union[Mapping[str, object], None] = None
    # Configure a custom httpx client. See the
    # [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
    http_client: Union[Any, None] = None
    """Optional httpx.Client. Only used for sync invocations. Must specify 
        http_async_client as well if you'd like a custom client for async invocations.
    """
    http_async_client: Union[Any, None] = None
    """Optional httpx.AsyncClient. Only used for async invocations. Must specify 
        http_client as well if you'd like a custom client for sync invocations."""

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    @root_validator(pre=True)
    def build_extra(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Build extra kwargs from additional params that were passed in."""
        all_required_field_names = get_pydantic_field_names(cls)
        extra = values.get("model_kwargs", {})
        for field_name in list(values):
            if field_name in extra:
                raise ValueError(f"Found {field_name} supplied twice.")
            if field_name not in all_required_field_names:
                warnings.warn(
                    f"""WARNING! {field_name} is not default parameter.
                    {field_name} was transferred to model_kwargs.
                    Please confirm that {field_name} is what you intended."""
                )
                extra[field_name] = values.pop(field_name)

        invalid_model_kwargs = all_required_field_names.intersection(extra.keys())
        if invalid_model_kwargs:
            raise ValueError(
                f"Parameters {invalid_model_kwargs} should be specified explicitly. "
                f"Instead they were passed in as part of `model_kwargs` parameter."
            )

        values["model_kwargs"] = extra
        return values

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""

        upstage_api_key = get_from_dict_or_env(
            values, "upstage_api_key", "UPSTAGE_API_KEY"
        )
        values["upstage_api_key"] = (
            convert_to_secret_str(upstage_api_key) if upstage_api_key else None
        )
        values["upstage_api_base"] = values["upstage_api_base"] or os.getenv(
            "UPSTAGE_API_BASE"
        )
        client_params = {
            "api_key": (
                values["upstage_api_key"].get_secret_value()
                if values["upstage_api_key"]
                else None
            ),
            "base_url": values["upstage_api_base"],
            "timeout": values["request_timeout"],
            "max_retries": values["max_retries"],
            "default_headers": values["default_headers"],
            "default_query": values["default_query"],
        }
        if not values.get("client"):
            sync_specific = {"http_client": values["http_client"]}
            values["client"] = openai.OpenAI(
                **client_params, **sync_specific
            ).embeddings
        if not values.get("async_client"):
            async_specific = {"http_client": values["http_async_client"]}
            values["async_client"] = openai.AsyncOpenAI(
                **client_params, **async_specific
            ).embeddings
        return values

    @property
    def _invocation_params(self) -> Dict[str, Any]:
        self.model = self.model.replace("-query", "").replace("-passage", "")

        params: Dict = {"model": self.model, **self.model_kwargs}
        if self.dimensions is not None:
            params["dimensions"] = self.dimensions
        return params

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document texts using passage model.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        assert (
            self.embed_batch_size <= MAX_EMBED_BATCH_SIZE
        ), f"The embed_batch_size should not be larger than {MAX_EMBED_BATCH_SIZE}."
        params = self._invocation_params
        params["model"] = params["model"] + "-passage"
        embeddings = []

        batch_size = min(self.embed_batch_size, len(texts))
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            data = self.client.create(input=batch, **params).data
            embeddings.extend([r.embedding for r in data])

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text using query model.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        params = self._invocation_params
        params["model"] = params["model"] + "-query"

        response = self.client.create(input=text, **params)

        if not isinstance(response, dict):
            response = response.model_dump()
        return response["data"][0]["embedding"]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document texts using passage model asynchronously.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        assert (
            self.embed_batch_size <= MAX_EMBED_BATCH_SIZE
        ), f"The embed_batch_size should not be larger than {MAX_EMBED_BATCH_SIZE}."
        params = self._invocation_params
        params["model"] = params["model"] + "-passage"
        embeddings = []

        batch_size = min(self.embed_batch_size, len(texts))
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self.async_client.create(input=batch, **params)
            embeddings.extend([r.embedding for r in response.data])
        return embeddings

    async def aembed_query(self, text: str) -> List[float]:
        """Asynchronous Embed query text using query model.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        params = self._invocation_params
        params["model"] = params["model"] + "-query"

        response = await self.async_client.create(input=text, **params)

        if not isinstance(response, dict):
            response = response.model_dump()
        return response["data"][0]["embedding"]
