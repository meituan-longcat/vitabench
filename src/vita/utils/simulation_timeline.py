"""
将一次 SimulationRun 的消息列表转为按顺序展示的 timeline 结构，供 Web 可视化使用。
"""
from __future__ import annotations

import copy
import json
from typing import Any, Optional

from vita.data_model.message import (
    AssistantMessage,
    MultiToolMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from vita.data_model.simulation import Results, SimulationRun


def _extract_reasoning(raw_data: Optional[dict]) -> Optional[str]:
    """从 LLM 原始响应中提取思维链（助手与用户模拟器共用同一套字段约定）。"""
    if not isinstance(raw_data, dict):
        return None
    msg = raw_data.get("message")
    for key in ("reasoning_content", "reasoning"):
        v = raw_data.get(key)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(msg, dict):
            v2 = msg.get(key)
            if isinstance(v2, str) and v2.strip():
                return v2
    return None


def _tool_calls_public(tc_list: Optional[list]) -> list[dict[str, Any]]:
    if not tc_list:
        return []
    out = []
    for tc in tc_list:
        if hasattr(tc, "model_dump"):
            d = tc.model_dump()
        elif isinstance(tc, dict):
            d = tc
        else:
            continue
        out.append(
            {
                "id": d.get("id", ""),
                "name": d.get("name", ""),
                "requestor": d.get("requestor", "assistant"),
                "arguments": d.get("arguments", {}),
            }
        )
    return out


def _redact_secret_value(value: Any) -> Any:
    if not isinstance(value, str):
        return "（已隐藏）"
    if len(value) > 16:
        return value[:10] + "…（已隐藏）"
    return "（已隐藏）"


def _redact_headers_for_display(headers: Optional[dict]) -> Optional[dict]:
    if not isinstance(headers, dict):
        return headers
    redacted = copy.deepcopy(headers)
    for key in list(redacted.keys()):
        lk = str(key).lower()
        if lk in ("authorization", "cookie", "x-api-key", "api-key"):
            redacted[key] = _redact_secret_value(redacted[key])
    return redacted


def _redact_request_json_for_display(payload: Optional[dict]) -> Optional[dict]:
    if not isinstance(payload, dict):
        return payload
    redacted = copy.deepcopy(payload)
    if isinstance(redacted.get("headers"), dict):
        redacted["headers"] = _redact_headers_for_display(redacted["headers"])
    for key in list(redacted.keys()):
        lk = str(key).lower()
        if lk in ("authorization", "cookie", "x-api-key", "api-key", "token"):
            redacted[key] = _redact_secret_value(redacted[key])
    return redacted


def _message_public_snapshot(msg: Any) -> dict[str, Any]:
    """用于“assistant 本轮接收信息”展示的简化快照。"""
    base = {
        "role": getattr(msg, "role", None),
        "turn_idx": getattr(msg, "turn_idx", None),
        "timestamp": getattr(msg, "timestamp", None),
    }
    if isinstance(msg, SystemMessage):
        return {**base, "kind": "system", "content": msg.content}
    if isinstance(msg, UserMessage):
        return {
            **base,
            "kind": "user",
            "content": msg.content,
            "tool_calls": _tool_calls_public(msg.tool_calls),
        }
    if isinstance(msg, AssistantMessage):
        return {
            **base,
            "kind": "assistant",
            "content": msg.content,
            "tool_calls": _tool_calls_public(msg.tool_calls),
        }
    if isinstance(msg, ToolMessage):
        return {
            **base,
            "kind": "tool",
            "tool_call_id": msg.id,
            "tool_name": msg.name,
            "requestor": msg.requestor,
            "content": msg.content,
            "error": msg.error,
        }
    if isinstance(msg, MultiToolMessage):
        return {
            **base,
            "kind": "multi_tool",
            "tool_results": [
                {
                    "tool_call_id": tm.id,
                    "tool_name": tm.name,
                    "requestor": tm.requestor,
                    "content": tm.content,
                    "error": tm.error,
                }
                for tm in msg.tool_messages
            ],
        }
    return {**base, "kind": "unknown", "repr": repr(msg)}


def _recorded_http_request(raw_data: Optional[dict]) -> Optional[dict[str, Any]]:
    if not isinstance(raw_data, dict):
        return None
    request = raw_data.get("_http_request") or raw_data.get("http_request")
    if not isinstance(request, dict):
        return None
    redacted = copy.deepcopy(request)
    redacted["source"] = redacted.get("source") or "recorded"
    redacted["headers"] = _redact_headers_for_display(redacted.get("headers"))
    redacted["json"] = _redact_request_json_for_display(redacted.get("json"))
    return redacted


def _recorded_http_response(raw_data: Optional[dict]) -> Optional[dict[str, Any]]:
    if not isinstance(raw_data, dict):
        return None
    response = raw_data.get("_http_response") or raw_data.get("http_response")
    if isinstance(response, dict):
        return copy.deepcopy(response)
    return {
        "source": "saved_choice_only",
        "json": copy.deepcopy(raw_data),
        "note": "This Results file stores only the selected response choice, not the full HTTP response object.",
    }


def _llm_info_for_role(results: Optional[Results], role: str):
    if results is None:
        return None
    if role == "user":
        return results.info.user_info
    if role == "assistant":
        return results.info.agent_info
    return None


def _reconstructed_http_request(
    results: Optional[Results],
    role: str,
    received_messages: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    info = _llm_info_for_role(results, role)
    if info is None:
        return None
    llm_args = _redact_request_json_for_display(getattr(info, "llm_args", None)) or {}
    request_json = copy.deepcopy(llm_args)
    base_url = request_json.pop("base_url", None)
    headers = request_json.pop("headers", None)
    request_json.update(
        {
            "model": getattr(info, "llm", None),
            "messages": received_messages,
            "stream": False,
        }
    )
    if role == "assistant":
        request_json["tools"] = "not stored in Results; available at runtime"
        request_json["tool_choice"] = "auto when tools are supplied"
    return {
        "source": "reconstructed",
        "method": "POST",
        "url": base_url,
        "headers": _redact_headers_for_display(headers),
        "json": request_json,
        "note": "The original HTTP request was not stored in this Results file; this view is reconstructed from saved context and run metadata.",
    }


def _http_request_snapshot(
    results: Optional[Results],
    role: str,
    received_messages: list[dict[str, Any]],
    raw_data: Optional[dict],
) -> Optional[dict[str, Any]]:
    return _recorded_http_request(raw_data) or _reconstructed_http_request(
        results, role, received_messages
    )


def _http_response_snapshot(raw_data: Optional[dict]) -> Optional[dict[str, Any]]:
    return _recorded_http_response(raw_data)


def build_timeline_from_simulation(
    simulation: SimulationRun, results: Optional[Results] = None
) -> list[dict[str, Any]]:
    """
    按 messages 顺序生成 timeline 条目；assistant 拆出思维链、正文、工具调用；tool 含结果与错误标记。
    """
    entries: list[dict[str, Any]] = []
    seq = 0
    for msg in simulation.messages:
        seq += 1
        base = {
            "seq": seq,
            "turn_idx": getattr(msg, "turn_idx", None),
            "timestamp": getattr(msg, "timestamp", None),
        }
        if isinstance(msg, SystemMessage):
            entries.append(
                {
                    **base,
                    "kind": "system",
                    "role": "system",
                    "content": msg.content,
                }
            )
        elif isinstance(msg, UserMessage):
            user_reasoning = _extract_reasoning(
                msg.raw_data if isinstance(msg.raw_data, dict) else None
            )
            received_messages = [
                _message_public_snapshot(m) for m in simulation.messages[: seq - 1]
            ]
            entries.append(
                {
                    **base,
                    "kind": "user",
                    "role": "user",
                    "reasoning": user_reasoning,
                    "content": msg.content,
                    "tool_calls": _tool_calls_public(msg.tool_calls),
                    "usage": msg.usage,
                    "cost": msg.cost,
                    "http_request": _http_request_snapshot(
                        results, "user", received_messages, msg.raw_data
                    ),
                    "http_response": _http_response_snapshot(msg.raw_data),
                    "raw_data": msg.raw_data,
                    "user_received_context": received_messages,
                }
            )
        elif isinstance(msg, AssistantMessage):
            reasoning = _extract_reasoning(
                msg.raw_data if isinstance(msg.raw_data, dict) else None
            )
            received_messages = [
                _message_public_snapshot(m) for m in simulation.messages[: seq - 1]
            ]
            entries.append(
                {
                    **base,
                    "kind": "assistant",
                    "role": "assistant",
                    "reasoning": reasoning,
                    "content": msg.content,
                    "tool_calls": _tool_calls_public(msg.tool_calls),
                    "usage": msg.usage,
                    "cost": msg.cost,
                    "http_request": _http_request_snapshot(
                        results, "assistant", received_messages, msg.raw_data
                    ),
                    "http_response": _http_response_snapshot(msg.raw_data),
                    "raw_data": msg.raw_data,
                    # 近似重建：assistant 在该轮生成前可见的历史消息（按顺序）
                    "assistant_received_context": received_messages,
                }
            )
        elif isinstance(msg, ToolMessage):
            entries.append(
                {
                    **base,
                    "kind": "tool",
                    "role": "tool",
                    "tool_call_id": msg.id,
                    "tool_name": msg.name,
                    "requestor": msg.requestor,
                    "content": msg.content,
                    "error": msg.error,
                }
            )
        elif isinstance(msg, MultiToolMessage):
            subs = []
            for tm in msg.tool_messages:
                subs.append(
                    {
                        "tool_call_id": tm.id,
                        "tool_name": tm.name,
                        "requestor": tm.requestor,
                        "content": tm.content,
                        "error": tm.error,
                    }
                )
            entries.append(
                {
                    **base,
                    "kind": "multi_tool",
                    "role": "tool",
                    "tool_results": subs,
                }
            )
        else:
            entries.append(
                {
                    **base,
                    "kind": "unknown",
                    "role": getattr(msg, "role", None),
                    "repr": repr(msg),
                }
            )
    return entries


def _redact_llm_args_for_display(llm_args: Optional[dict]) -> Optional[dict]:
    """脱敏后展示 llm_args（避免把 Authorization 等原样打到页面上）。"""
    if not llm_args:
        return None
    d = copy.deepcopy(llm_args)
    d["headers"] = _redact_headers_for_display(d.get("headers"))
    return d


def build_user_simulator_profile(results: Results, task_id: str) -> dict[str, Any]:
    """
    汇总 User Simulator 的角色设定来源：
    - results.info.user_info：实现类型、所用 LLM、全局用户模拟器说明模板
    - 对应 Task：user_scenario（人设/情境）、instructions（本任务要用户通过对话传达给智能体的指令）
    - 与运行时一致：用 str(user_profile) + instructions 对模板做 .format，得到实际 system prompt
    """
    ui = results.info.user_info
    base: dict[str, Any] = {
        "implementation": ui.implementation,
        "llm": ui.llm,
        "llm_args": _redact_llm_args_for_display(ui.llm_args),
        "global_simulation_guidelines_template": ui.global_simulation_guidelines,
    }
    task = next((t for t in results.tasks if t.id == task_id), None)
    if task is None:
        base["task_found"] = False
        base["note"] = f"未在 results.tasks 中找到 task_id={task_id}，仅展示 info.user_info。"
        return base

    base["task_found"] = True
    base["task_id"] = task.id
    base["domain"] = task.domain
    base["user_scenario"] = task.user_scenario.model_dump(mode="json")
    base["instructions"] = task.instructions

    # 与 UserSimulator.system_prompt / run.py 中 UserConstructor 一致
    persona_runtime = str(task.user_scenario.user_profile)
    instructions_runtime = str(task.instructions)
    base["persona_runtime_string"] = persona_runtime

    tpl = ui.global_simulation_guidelines or ""
    rendered: Optional[str] = None
    render_error: Optional[str] = None
    if tpl:
        try:
            rendered = tpl.format(
                persona=persona_runtime,
                instructions=instructions_runtime,
            )
        except (KeyError, ValueError) as e:
            render_error = f"{type(e).__name__}: {e}"
    base["rendered_user_system_prompt"] = rendered
    base["rendered_system_prompt_error"] = render_error

    return base


def simulation_run_summary(simulation: SimulationRun) -> dict[str, Any]:
    return {
        "id": simulation.id,
        "task_id": simulation.task_id,
        "trial": simulation.trial,
        "seed": simulation.seed,
        "termination_reason": str(simulation.termination_reason),
        "start_time": simulation.start_time,
        "end_time": simulation.end_time,
        "duration": simulation.duration,
        "agent_cost": simulation.agent_cost,
        "user_cost": simulation.user_cost,
        "reward": simulation.reward_info.reward
        if simulation.reward_info
        else None,
        "message_count": len(simulation.messages),
    }


def format_json_for_display(obj: Any, max_chars: int = 120_000) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, indent=2)
    except TypeError:
        s = str(obj)
    if len(s) > max_chars:
        return s[:max_chars] + f"\n\n…（已截断，共 {len(s)} 字符）"
    return s
