"""
Adapted from https://github.com/BerriAI/appl/blob/main/appl/core/tool.py
and modified to fit the needs of the project.
"""

import inspect
from abc import ABC, abstractmethod
from inspect import Signature
from typing import Dict, Any, List, Optional, Callable

from docstring_parser import parse
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, create_model, field_serializer
from typing_extensions import override


class BaseTool(BaseModel, ABC):
    """The base class for a Tool that can be called by LLMs."""

    name: str = Field(..., description="The name of the Tool")
    """The name of the Tool."""

    @property
    @abstractmethod
    def openai_schema(self) -> Dict[str, Any]:
        """Get the OpenAI schema of the tool."""
        raise NotImplementedError

    @abstractmethod
    def _call(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the tool."""
        return self._call(*args, **kwargs)


class Tool(BaseTool):
    """The Tool built from a Python function, can be called by LLMs."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    short_desc: str = Field("", description="The short description of the Tool")
    """The short description of the Tool."""
    long_desc: str = Field("", description="The long description of the Tool")
    """The long description of the Tool."""
    params: type[BaseModel] = Field(..., description="The parameters of the Tool")
    """The parameters of the Tool."""
    returns: type[BaseModel] = Field(..., description="The return of the Tool")
    """The return of the Tool."""
    raises: List[Dict[str, Optional[str]]] = Field(
        [], description="The exceptions raised by the Tool"
    )
    """The exceptions raised by the Tool."""
    examples: List[str] = Field([], description="The examples of the Tool")
    """The examples of the Tool."""
    info: Dict = Field({}, description="Additional information of the Tool")
    """Additional information of the Tool."""

    def __init__(self, func: Callable, use_short_desc: bool = False, **predefined: Any):
        """Create a tool from a function.

        Args:
            func: The function to create the tool from.
            use_short_desc:
                Whether to use the short description instead of the full description.
            predefined: Additional arguments for the tool.
        """
        name = func.__name__
        sig = inspect.signature(func)
        doc = func.__doc__
        super().__init__(name=name, **self.parse_data(sig, doc, predefined))
        self._use_short_desc = use_short_desc
        self._predefined = predefined
        self._func = func
        self.__name__ = name
        self.__signature__ = sig
        self.__doc__ = doc

    @classmethod
    def parse_data(
        cls, sig: Signature, docstring: Optional[str], predefined: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse data from the signature and docstring of a function."""
        doc = parse(docstring or "")
        data: Dict[str, Any] = {
            "short_desc": doc.short_description or "",
            "long_desc": doc.long_description or "",
        }

        params = {}
        doc_param = {p.arg_name: p for p in doc.params}
        for name, param in sig.parameters.items():
            anno = param.annotation
            default = param.default

            if default is param.empty:
                default = ...
            if name in doc_param:
                default = Field(default, description=doc_param[name].description)
                if (anno is param.empty) and (doc_param[name].type_name is not None):
                    anno = doc_param[name].type_name
            if anno is param.empty:
                anno = Any
            if name not in predefined:
                params[name] = (anno, default)
        data["params"] = create_model("parameters", **params)

        anno = sig.return_annotation
        if anno is sig.empty:
            if (doc.returns is not None) and (doc.returns.type_name is not None):
                anno = doc.returns.type_name
            else:
                anno = Any
        default = ...
        if doc.returns is not None:
            default = Field(..., description=doc.returns.description)
        data["returns"] = create_model("returns", returns=(anno, default))

        data["raises"] = [
            {"type": exc.type_name, "desc": exc.description} for exc in doc.raises
        ]

        data["examples"] = doc.examples
        return data

    @override
    @property
    def openai_schema(self) -> dict:
        """Get the OpenAI schema of the tool."""
        schema = self.params.model_json_schema()

        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                # Handle anyOf schemas (usually for Optional types)
                if "anyOf" in prop_schema:
                    type_info = None
                    items_schema = None
                    for option in prop_schema["anyOf"]:
                        if "type" in option:
                            type_info = option["type"]
                            # If it's an array type, extract the items schema
                            if type_info == "array" and "items" in option:
                                items_schema = option["items"]
                            break
                    
                    cleaned_schema = {k: v for k, v in prop_schema.items() if k != "anyOf"}
                    if type_info:
                        cleaned_schema["type"] = type_info
                        # Add items schema for array types
                        if type_info == "array" and items_schema:
                            cleaned_schema["items"] = items_schema
                    
                    schema["properties"][prop_name] = cleaned_schema
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self._get_description(),
                "parameters": schema,
            },
        }

    def to_str(self) -> str:
        """Represent the tool as a string."""
        s = f"def {self.name}{self.__signature__}:\n"
        s += f'    """{self.__doc__}"""'
        return s

    def _get_description(self):
        if not self.short_desc:
            logger.warning(f"Tool {self.name} has no description.")
            return self.name

        if (not self.long_desc) or self._use_short_desc:
            return self.short_desc

        return self.short_desc + "\n\n" + self.long_desc

    @field_serializer("params", when_used="json")
    def _serialize_params(self, params: type[BaseModel]) -> dict:
        return params.model_json_schema()

    @field_serializer("returns", when_used="json")
    def _serialize_returns(self, returns: type[BaseModel]) -> dict:
        return returns.model_json_schema()

    def __str__(self) -> str:
        return self.to_str()

    @override
    def _call(self, *args: Any, **kwargs: Any) -> Any:
        kwargs.update(self._predefined)
        return self._func(*args, **kwargs)


def as_tool(func: Callable, **kwargs: Any) -> Tool:
    """Wrap a given function with additional predefined arguments into a Tool.

    This function allows converting a standard function into a 'Tool' by
    specifying the function and any additional arguments that should be
    pre-defined for it. These additional arguments are passed as keyword
    arguments and will be bound to the function within the Tool object,
    so that these arguments are not required when using this tool.

    Args:
        func (Callable):
            The function to be converted into a Tool.
        **kwargs:
            Keyword arguments that will be predefined for the function in
            the Tool object.

    Returns:
        Tool:
            An object encapsulating the given function and its predefined
            arguments, ready to be utilized as a Tool.

    Examples:
        Given a function `move_disk` that requires an environment and two
        pegs to move a disk from one peg to another in the Tower of Hanoi
        puzzle, one can create a tool with a predefined environment by:

        ```python
        def move_disk(env: HanoiEnv, from_peg: int, to_peg: int) -> str:
            pass

        env = HanoiEnv()
        tools = [as_tool(move_disk, env=env)]
        ```

        In this example, `move_disk` is encapsulated into a Tool with `env`
        predefined, so only `from_peg` and `to_peg` are required.
    """
    return Tool(func=func, **kwargs)
