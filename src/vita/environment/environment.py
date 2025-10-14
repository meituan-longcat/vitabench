import json
import traceback
import inspect
import types
from datetime import date, datetime
from typing import Any, Literal, Optional

from loguru import logger
from pydantic import BaseModel, Field

from vita.data_model.message import (
    AssistantMessage,
    Message,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from vita.data_model.tasks import EnvAssertion, EnvFunctionCall, Task
from vita.environment.db import DB, MergedDB
from vita.environment.tool import Tool
from vita.environment.toolkit import ToolKitBase, ToolSignature, get_tool_signatures

from vita.utils.utils import get_task_file_path
from vita.prompts import get_prompts

def get_agent_policy(language: str = None) -> str:
    """Get agent policy based on language"""
    prompts = get_prompts(language)
    return prompts.agent_system_prompt


class EnvironmentInfo(BaseModel):
    """
    Environment information.
    """

    domain_name: str = Field(description="The name of the domain.")
    tool_defs: Optional[dict[str, ToolSignature]] = Field(
        description="The tool definitions of the environment.", default=None
    )


class Environment:
    """
    Environment
    """

    def __init__(
        self,
        domain_name: str,
        policy: str = None,
        tools: Optional[ToolKitBase] = None,
    ):
        """
        Environment
        Args:
            domain_name: The name of the domain.
            policy: The policy of the domain.
            tools: The tools available to the assistant in the domain.
        """
        self.domain_name = domain_name
        self.policy = policy if policy is not None else get_agent_policy()
        self.tools = tools

    def get_domain_name(self) -> str:
        """
        Get the name of the domain.
        """
        return self.domain_name

    def get_policy(self) -> str:
        """
        Get the policy of the domain.
        """
        return self.policy

    def get_tools(self) -> list[Tool]:
        """
        Get the tools of the domain.
        """
        if self.tools is None:
            raise ValueError("Tools not available")
        return list(self.tools.get_tools().values())

    def get_tools_description(
        self, env_type: Literal["assistant"]
    ) -> Optional[str]:
        """
        Return a description of the assistant tools.
        """
        if env_type != "assistant":
            raise ValueError(f"Invalid environment type: {env_type}")
        if self.tools is None:
            return None
        tools = sorted(self.tools.get_tools().values(), key=lambda x: x.name)
        return "\n\n".join(
            [f"{i + 1}. {t.name}\n{t.short_desc}" for i, t in enumerate(tools)]
        )

    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Use a tool available to the assistant of the domain.
        """
        if self.tools is None:
            raise ValueError("Tools not available")
        return self.tools.use_tool(tool_name=tool_name, **kwargs)

    def make_tool_call(
        self,
        tool_name: str,
        requestor: Literal["assistant"] = "assistant",
        **kwargs,
    ) -> Any:
        """
        Make a tool call based on the requestor.
        Args:
            tool_name: The name of the tool to call.
            requestor: The requestor of the tool call.
            kwargs: The arguments to pass to the tool.
        Returns:
            The response of the tool call.


        """
        if requestor != "assistant":
            raise ValueError(f"Invalid requestor: {requestor}. Only 'assistant' is supported.")
        return self.use_tool(tool_name=tool_name, **kwargs)

    def run_env_function_call(self, env_function_call: EnvFunctionCall) -> Any:
        """
        Runs any function available on agent environment.
        """
        env_type = env_function_call.env_type
        func_name = env_function_call.func_name
        if env_type != "assistant":
            raise ValueError(f"Invalid environment type: {env_type}. Only 'assistant' is supported.")
        if self.tools is None:
            raise ValueError("Tools not available")
        func = getattr(self.tools, func_name)
        if func is None:
            raise ValueError(f"Function {func_name} not found in assistant tools")
        res = func(**env_function_call.arguments)
        return res

    def run_env_assertion(
        self,
        assertion: EnvAssertion,
        raise_assertion_error: bool = True,
    ) -> bool:
        """
        Runs any assertion function on agent tools or user tools.
        """
        if not isinstance(assertion, EnvAssertion):
            raise ValueError(f"Assertion must be an EnvAssertion. Got {assertion}")
        res = self.run_env_function_call(assertion)
        if not isinstance(res, bool):
            raise ValueError(
                f"Function {assertion.func_name} returned {type(res)} instead of bool"
            )
        assert_pass = res == assertion.assert_value
        if raise_assertion_error:
            assert assert_pass, assertion.message or f"Assertion failed: {assertion}"
        return assert_pass

    def run_env_function_calls(self, env_function_calls: list[EnvFunctionCall]) -> None:
        """
        Run a list of environment function calls. If the function call is an assertion,
        an assertion check will be performed.
        """
        for env_function_call in env_function_calls:
            if isinstance(env_function_call, EnvAssertion):
                self.run_env_assertion(env_function_call, raise_assertion_error=True)
            else:
                self.run_env_function_call(env_function_call)

    def get_info(self, include_tool_info: bool = False) -> EnvironmentInfo:
        """
        Get environment information.
        """
        return EnvironmentInfo(
            domain_name=self.domain_name,
            policy=self.policy,
            tool_defs=(
                get_tool_signatures(self.tools)
                if self.tools is not None and include_tool_info
                else None
            ),
        )

    def check_db(self, reference: DB) -> bool:
        """
        Compare the agent database with the reference
        """
        return self.get_db_hash() == reference.get_hash()

    def get_db_hash(self) -> Optional[str]:
        """
        Get a hash of the agent database
        Returns None if the database is not available
        """
        if self.tools is None:
            return None
        return self.tools.get_db_hash()

    @classmethod
    def to_json_str(cls, resp: Any) -> str:
        """
        Convert a response to a JSON string.
        """

        def _process(resp: Any) -> str:
            if isinstance(resp, BaseModel):
                return resp.model_dump()
            elif isinstance(resp, str):
                return resp
            elif resp is None:
                return resp
            elif isinstance(resp, (int, float, bool)):
                return str(resp)
            elif isinstance(resp, list):
                return [_process(item) for item in resp]
            elif isinstance(resp, tuple):
                return tuple(_process(item) for item in resp)
            elif isinstance(resp, dict):
                return {k: _process(v) for k, v in resp.items()}
            elif isinstance(resp, (datetime, date)):
                return resp.isoformat()
            else:
                raise ValueError(f"Unsupported type: {type(resp)}")

        if not isinstance(resp, str):
            return json.dumps(_process(resp), default=str, ensure_ascii=False)
        return resp

    def get_response(self, message: ToolCall) -> ToolMessage:
        """
        Get the response of the domain.
        Args:
            message: The message to get the response for.
        Returns:
            The response of the tool call.
        """
        error = False
        try:
            resp = self.make_tool_call(
                message.name, requestor=message.requestor, **message.arguments
            )
        except Exception as e:
            traceback.print_exc()
            resp = f"Error: {e}"
            error = True
        logger.debug(f"Response: {resp}")
        resp = self.to_json_str(resp)
        return ToolMessage(
            id=message.id,
            name=message.name,
            content=resp,
            requestor=message.requestor,
            role="tool",
            error=error,
        )


def copy_function_metadata(original_func, new_func):
    """Copy function metadata, including decorator information"""
    attrs_to_copy = [
        '__name__', '__doc__', '__module__', '__qualname__',
        '__annotations__', '__dict__'
    ]

    for attr in attrs_to_copy:
        if hasattr(original_func, attr):
            try:
                setattr(new_func, attr, getattr(original_func, attr))
            except (AttributeError, TypeError):
                pass

    if hasattr(original_func, '__wrapped__'):
        new_func.__wrapped__ = original_func.__wrapped__

    return new_func


def get_cross_environment(
    domain: str,
    environment: dict = {},
    language: str = None,
) -> Environment:
    from vita.registry import registry

    original_env_list = []
    for domain_str in domain.split(","):
        environment_constructor = registry.get_env_constructor(domain_str)
        original_env_list.append(environment_constructor(environment, language))
    
    tools = ToolKitBase()

    for env in original_env_list:
        if not hasattr(env, 'tools') or env.tools is None:
            continue
            
        env_tools = env.tools
        
        if hasattr(env_tools, '_func_tools'):
            func_tools = env_tools._func_tools
            for tool_name, tool_func in func_tools.items():
                if not hasattr(tools, tool_name):
                    if inspect.ismethod(tool_func):
                        bound_method = types.MethodType(tool_func.__func__, tools)
                        setattr(tools, tool_name, bound_method)
                    elif inspect.isfunction(tool_func):
                        bound_method = types.MethodType(tool_func, tools)
                        setattr(tools, tool_name, bound_method)
                    else:
                        setattr(tools, tool_name, tool_func)
        
        for attr_name in dir(env_tools):
            if attr_name.startswith('__'):
                continue
                
            try:
                attr = getattr(env_tools, attr_name)
                if callable(attr) and (hasattr(attr, '__tool__') or attr_name.startswith('_')):
                    if not hasattr(tools, attr_name):
                        if inspect.ismethod(attr):
                            bound_method = types.MethodType(attr.__func__, tools)
                            setattr(tools, attr_name, bound_method)
                        elif inspect.isfunction(attr):
                            bound_method = types.MethodType(attr, tools)
                            setattr(tools, attr_name, bound_method)
                        else:
                            setattr(tools, attr_name, attr)
            except (AttributeError, TypeError):
                continue

    merged_db = None
    for env in original_env_list:
        if hasattr(env, 'tools') and env.tools is not None and hasattr(env.tools, 'db') and env.tools.db is not None:
            if merged_db is None:
                merged_db = MergedDB()
                merged_db.add_db(env.tools.db)
            else:
                merged_db.add_db(env.tools.db)

    if merged_db is not None:
        tools.db = merged_db

    return Environment(
        domain_name=domain,
        policy=get_agent_policy(language),
        tools=tools,
    )


def get_cross_tasks(language: str = None) -> list[Task]:
    task_path = get_task_file_path("cross_domain", language)
    with open(task_path, "r") as fp:
        tasks = json.load(fp)
    return [Task.model_validate(task) for task in tasks]
