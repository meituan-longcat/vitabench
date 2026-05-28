import json
import re
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from vita.data_model.message import ToolCall
from vita.data_model.simulation import Results
from vita.environment.environment import get_cross_environment
from vita.metrics.agent_metrics import compute_metrics
from vita.registry import registry
from vita.utils.simulation_timeline import (
    build_timeline_from_simulation,
    build_user_simulator_profile,
    format_json_for_display,
    simulation_run_summary,
)
from vita.utils.task_sorting import simulation_sort_key, task_id_sort_key
from vita.utils.utils import DATA_DIR


def _simulations_dir() -> Path:
    return DATA_DIR / "simulations"


def _allowed_simulation_roots() -> list[Path]:
    roots = [_simulations_dir().resolve()]
    share_root = Path(
        "/vePFS-Mindverse/share/mutian/vitabench/vitabench/data/simulations"
    )
    if share_root.exists():
        roots.append(share_root.resolve())
    return roots


def _benchmark_simulations_dir() -> Path:
    return _simulations_dir() / "benchmark_runs"


def _benchmark_logs_dir(base_logs_dir: Path) -> Path:
    benchmark_dir = base_logs_dir / "benchmark_runs"
    if benchmark_dir.exists() or not base_logs_dir.name == "benchmark_runs":
        return benchmark_dir
    return base_logs_dir


BENCHMARK_SPLITS = [
    {
        "key": "delivery",
        "label": "delivery",
        "domain": "delivery",
        "log_names": ["delivery.log"],
        "result_names": ["delivery.json"],
    },
    {
        "key": "ota",
        "label": "ota",
        "domain": "ota",
        "log_names": ["ota.log"],
        "result_names": ["ota.json"],
    },
    {
        "key": "instore",
        "label": "instore",
        "domain": "instore",
        "log_names": ["instore.log"],
        "result_names": ["instore.json"],
    },
    {
        "key": "cross",
        "label": "cross",
        "domain": "delivery,instore,ota",
        "log_names": ["cross.log", "delivery,instore,ota.log"],
        "result_names": ["cross.json", "delivery,instore,ota.json"],
    },
]


def _resolve_simulation_file(file: str) -> Path:
    """仅允许读取 data/simulations 下的 .json 相对路径，防止路径穿越。"""
    if not file or "\\" in file:
        raise HTTPException(status_code=400, detail="invalid simulation file path")
    rel = Path(file)
    if not file.endswith(".json"):
        raise HTTPException(status_code=400, detail="simulation file must end with .json")
    if rel.is_absolute():
        path = rel.resolve()
    else:
        if any(part in ("", ".", "..") for part in rel.parts):
            raise HTTPException(status_code=400, detail="invalid simulation file path")
        if any(part.startswith(".") for part in rel.parts):
            raise HTTPException(status_code=400, detail="invalid simulation file path")
        roots = _allowed_simulation_roots()
        path = (roots[0] / rel).resolve()
        for root in roots:
            candidate = (root / rel).resolve()
            if candidate.exists():
                path = candidate
                break
    for root in _allowed_simulation_roots():
        try:
            path.relative_to(root)
            break
        except ValueError:
            continue
    else:
        raise HTTPException(status_code=403, detail="path outside allowed simulations dirs")
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"simulation file not found: {file}")
    return path


def _load_events(file_path: Path) -> list[dict]:
    events = []
    with open(file_path, "r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _safe_child_dir(root: Path, name: str, label: str) -> Path:
    if not name or "\\" in name:
        raise HTTPException(status_code=400, detail=f"invalid {label}")
    rel = Path(name)
    if rel.is_absolute() or len(rel.parts) != 1 or rel.parts[0] in (".", ".."):
        raise HTTPException(status_code=400, detail=f"invalid {label}")
    if rel.name.startswith("."):
        raise HTTPException(status_code=400, detail=f"invalid {label}")
    path = (root / rel.name).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=f"{label} outside root") from exc
    return path


def _read_tail(path: Optional[Path], max_bytes: int = 256_000) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    size = path.stat().st_size
    with open(path, "rb") as fp:
        if size > max_bytes:
            fp.seek(size - max_bytes)
            fp.readline()
        return fp.read().decode("utf-8", errors="replace")


def _count_completed_from_log(path: Optional[Path]) -> int:
    if path is None or not path.exists() or not path.is_file():
        return 0
    task_ids = set()
    pattern = re.compile(r"Orchestrator\.run 结束 task_id=([^\s]+)")
    with open(path, "r", encoding="utf-8", errors="replace") as fp:
        for line in fp:
            match = pattern.search(line)
            if match:
                task_ids.add(match.group(1))
    return len(task_ids)


def _split_file(base_dir: Optional[Path], names: list[str]) -> Optional[Path]:
    if base_dir is None or not base_dir.exists():
        return None
    for name in names:
        path = base_dir / name
        if path.exists():
            return path
    return None


def _result_path_from_log(path: Optional[Path]) -> Optional[Path]:
    if path is None or not path.exists() or not path.is_file():
        return None
    found = None
    pattern = re.compile(r"save_to=([^\s]+\.json)")
    with open(path, "r", encoding="utf-8", errors="replace") as fp:
        for line in fp:
            match = pattern.search(line)
            if match:
                found = Path(match.group(1))
    if found is not None and found.is_absolute() and found.exists():
        return found
    return None


def _load_result_summary(path: Optional[Path], include_metrics: bool = True) -> dict:
    if path is None or not path.exists():
        return {}
    if not include_metrics:
        return {"samples": 100, "tasks": 100}
    try:
        results = Results.load(path)
        metrics = compute_metrics(results)
        return {
            "samples": len(results.simulations),
            "tasks": len(results.tasks),
            "avg_reward": metrics.avg_reward,
            "pass1": metrics.pass_hat_ks.get(1),
            "duration_sec": metrics.total_duration,
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _simulation_view_file(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    resolved = path.resolve()
    for root in _allowed_simulation_roots():
        try:
            return resolved.relative_to(root).as_posix()
        except ValueError:
            continue
    return str(resolved)


def _split_summary(
    run_name: str,
    split: dict,
    logs_dir: Optional[Path],
    simulations_dir: Optional[Path],
    include_metrics: bool = True,
) -> dict:
    log_path = _split_file(logs_dir, split["log_names"])
    result_path = _split_file(simulations_dir, split["result_names"]) or _result_path_from_log(log_path)
    result = _load_result_summary(result_path, include_metrics=include_metrics)
    expected = int(result.get("tasks") or 100)
    completed = max(
        int(result.get("samples") or 0),
        int(_count_completed_from_log(log_path) or 0),
    )
    completed = min(completed, expected)
    tail = _read_tail(log_path, max_bytes=96_000)
    has_success_marker = "Successfully completed all simulations!" in tail
    is_recent = bool(log_path and log_path.exists() and time.time() - log_path.stat().st_mtime < 300)
    has_complete_result = bool(
        result_path and result_path.exists() and "error" not in result and completed >= expected
    )
    status = "pending"
    if has_complete_result or has_success_marker:
        status = "complete"
        completed = expected
    elif is_recent:
        status = "running"
    elif re.search(r"(FAILED|Fatal|Error loading|HTTPError)", tail):
        status = "failed"
    elif log_path and log_path.exists():
        status = "running"
    mtime_candidates = [
        p.stat().st_mtime
        for p in (log_path, result_path)
        if p is not None and p.exists()
    ]
    return {
        "run_name": run_name,
        "key": split["key"],
        "label": split["label"],
        "domain": split["domain"],
        "status": status,
        "completed": completed,
        "expected": expected,
        "progress": completed / expected if expected else 0,
        "log_file": log_path.name if log_path else None,
        "log_size": log_path.stat().st_size if log_path else 0,
        "log_mtime": log_path.stat().st_mtime if log_path else None,
        "result_file": str(result_path) if result_path and result_path.is_absolute() else (result_path.name if result_path else None),
        "result_view_file": _simulation_view_file(result_path),
        "result_size": result_path.stat().st_size if result_path else 0,
        "result_mtime": result_path.stat().st_mtime if result_path else None,
        "mtime": max(mtime_candidates) if mtime_candidates else None,
        "metrics": result,
    }


def _extra_split_summaries(
    run_name: str,
    logs_dir: Optional[Path],
    simulations_dir: Optional[Path],
    known_log_names: set[str],
    known_result_names: set[str],
) -> list[dict]:
    extras = []
    if logs_dir and logs_dir.exists():
        for path in sorted(logs_dir.glob("*.log")):
            if path.name in known_log_names:
                continue
            stem = path.stem
            extras.append(
                _split_summary(
                    run_name,
                    {
                        "key": stem,
                        "label": stem,
                        "domain": stem,
                        "log_names": [path.name],
                        "result_names": [f"{stem}.json"],
                    },
                    logs_dir,
                    simulations_dir,
                    include_metrics=False,
                )
            )
    if simulations_dir and simulations_dir.exists():
        existing_keys = {row["key"] for row in extras}
        for path in sorted(simulations_dir.glob("*.json")):
            if path.name in known_result_names or path.stem in existing_keys:
                continue
            stem = path.stem
            extras.append(
                _split_summary(
                    run_name,
                    {
                        "key": stem,
                        "label": stem,
                        "domain": stem,
                        "log_names": [f"{stem}.log"],
                        "result_names": [path.name],
                    },
                    logs_dir,
                    simulations_dir,
                    include_metrics=False,
                )
            )
    return extras


def _benchmark_run_summary(
    run_name: str,
    benchmark_logs_root: Path,
    benchmark_sim_root: Path,
    include_metrics: bool = True,
) -> dict:
    logs_dir = benchmark_logs_root / run_name
    simulations_dir = benchmark_sim_root / run_name
    known_log_names = {name for split in BENCHMARK_SPLITS for name in split["log_names"]}
    known_result_names = {
        name for split in BENCHMARK_SPLITS for name in split["result_names"]
    }
    splits = [
        _split_summary(
            run_name,
            split,
            logs_dir,
            simulations_dir,
            include_metrics=include_metrics,
        )
        for split in BENCHMARK_SPLITS
    ]
    splits.extend(
        _extra_split_summaries(
            run_name, logs_dir, simulations_dir, known_log_names, known_result_names
        )
    )
    visible = [s for s in splits if s["status"] != "pending" or s["completed"] > 0]
    status_values = [s["status"] for s in visible]
    if not visible:
        status = "pending"
    elif any(s == "running" for s in status_values):
        status = "running"
    elif any(s == "failed" for s in status_values):
        status = "failed"
    elif all(s == "complete" for s in status_values) and len(visible) >= 4:
        status = "complete"
    else:
        status = "partial"
    mtimes = [s["mtime"] for s in visible if s["mtime"] is not None]
    completed_samples = sum(int(s["completed"]) for s in splits)
    expected_samples = sum(int(s["expected"]) for s in splits) or 400
    completed_splits = sum(1 for s in visible if s["status"] == "complete")
    return {
        "run_name": run_name,
        "status": status,
        "completed_splits": completed_splits,
        "total_splits": max(len(visible), 4),
        "completed_samples": completed_samples,
        "expected_samples": expected_samples,
        "progress": completed_samples / expected_samples if expected_samples else 0,
        "last_update": max(mtimes) if mtimes else None,
        "age_seconds": (time.time() - max(mtimes)) if mtimes else None,
        "logs_dir": str(logs_dir) if logs_dir.exists() else None,
        "simulations_dir": str(simulations_dir) if simulations_dir.exists() else None,
        "splits": splits,
    }


def _run_dir_mtime(run_name: str, benchmark_logs_root: Path, benchmark_sim_root: Path) -> float:
    mtimes = []
    for root in (benchmark_logs_root, benchmark_sim_root):
        path = root / run_name
        if path.exists():
            mtimes.append(path.stat().st_mtime)
            for child in path.glob("*"):
                if child.is_file():
                    mtimes.append(child.stat().st_mtime)
    return max(mtimes) if mtimes else 0.0


class ToolInvokeRequest(BaseModel):
    file: str
    sim_index: int
    tool_name: str
    arguments: dict = {}


def _resolve_task_from_simulation(results: Results, sim_index: int):
    if sim_index >= len(results.simulations):
        raise HTTPException(
            status_code=400,
            detail=f"sim_index out of range: {sim_index} (have {len(results.simulations)} simulations)",
        )
    sim = results.simulations[sim_index]
    task = next((t for t in results.tasks if t.id == sim.task_id), None)
    if task is None:
        raise HTTPException(
            status_code=404, detail=f"task not found in results.tasks: {sim.task_id}"
        )
    return sim, task


def _build_environment_for_task(task, language: str = "chinese"):
    if "," in task.domain:
        return get_cross_environment(task.domain, task.environment, language)
    env_constructor = registry.get_env_constructor(task.domain)
    return env_constructor(task.environment, language)


def _sorted_simulation_rows(results: Results) -> list[tuple[int, object]]:
    return sorted(enumerate(results.simulations), key=lambda row: simulation_sort_key(row[1]))


def _trial_sort_key(trial: object) -> int:
    try:
        return int(trial)
    except (TypeError, ValueError):
        return -1


def _is_non_full_reward(sim) -> bool:
    if sim.reward_info is None:
        return True
    try:
        return float(sim.reward_info.reward) < 1.0
    except (TypeError, ValueError):
        return True


def create_app(logs_dir: Optional[str] = None) -> FastAPI:
    app = FastAPI(title="VitaBench Log Viewer")
    base_logs_dir = Path(logs_dir) if logs_dir else DATA_DIR / "logs"
    static_dir = Path(__file__).parents[1] / "web"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        p = static_dir / "dashboard.html"
        if not p.exists():
            raise HTTPException(status_code=404, detail="dashboard.html not found")
        return p.read_text(encoding="utf-8")

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard_page() -> str:
        p = static_dir / "dashboard.html"
        if not p.exists():
            raise HTTPException(status_code=404, detail="dashboard.html not found")
        return p.read_text(encoding="utf-8")

    @app.get("/events", response_class=HTMLResponse)
    def events_page() -> str:
        p = static_dir / "index.html"
        if not p.exists():
            raise HTTPException(status_code=404, detail="index.html not found")
        return p.read_text(encoding="utf-8")

    @app.get("/trajectory", response_class=HTMLResponse)
    def trajectory_page() -> str:
        p = static_dir / "trajectory.html"
        if not p.exists():
            raise HTTPException(status_code=404, detail="trajectory.html not found")
        return p.read_text(encoding="utf-8")

    @app.get("/toolbox", response_class=HTMLResponse)
    def toolbox_page() -> str:
        p = static_dir / "tools.html"
        if not p.exists():
            raise HTTPException(status_code=404, detail="tools.html not found")
        return p.read_text(encoding="utf-8")

    @app.get("/api/benchmark-runs")
    def benchmark_runs(
        run_name: Optional[str] = Query(None),
        limit: int = Query(80, ge=1, le=500),
    ) -> dict:
        benchmark_logs_root = _benchmark_logs_dir(base_logs_dir)
        benchmark_sim_root = _benchmark_simulations_dir()
        run_names = set()
        for root in (benchmark_logs_root, benchmark_sim_root):
            if root.exists():
                run_names.update(p.name for p in root.iterdir() if p.is_dir())
        if run_name:
            _safe_child_dir(benchmark_logs_root, run_name, "run_name")
            run_names = {run_name}
        else:
            run_names = set(
                sorted(
                    run_names,
                    key=lambda name: _run_dir_mtime(
                        name, benchmark_logs_root, benchmark_sim_root
                    ),
                    reverse=True,
                )[:limit]
            )
        runs = [
            _benchmark_run_summary(
                name,
                benchmark_logs_root,
                benchmark_sim_root,
                include_metrics=run_name is not None,
            )
            for name in run_names
        ]
        runs.sort(key=lambda r: r["last_update"] or 0, reverse=True)
        return {
            "runs": runs,
            "logs_root": str(benchmark_logs_root),
            "simulations_root": str(benchmark_sim_root),
        }

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/benchmark-log", response_class=PlainTextResponse)
    def benchmark_log(
        run_name: str = Query(...),
        split: str = Query(...),
        lines: int = Query(300, ge=1, le=5000),
    ) -> str:
        benchmark_logs_root = _benchmark_logs_dir(base_logs_dir)
        run_dir = _safe_child_dir(benchmark_logs_root, run_name, "run_name")
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"run log dir not found: {run_name}")
        split_defs = {
            s["key"]: s
            for s in BENCHMARK_SPLITS
        }
        split_def = split_defs.get(split)
        if split_def is None:
            if not re.fullmatch(r"[A-Za-z0-9_.=,-]+", split):
                raise HTTPException(status_code=400, detail="invalid split")
            split_def = {"log_names": [f"{split}.log"]}
        path = _split_file(run_dir, split_def["log_names"])
        if path is None or not path.exists():
            raise HTTPException(status_code=404, detail=f"log not found: {split}")
        text = _read_tail(path, max_bytes=1_000_000)
        tail_lines = text.splitlines()[-lines:]
        return "\n".join(tail_lines)

    @app.get("/api/runs")
    def list_runs() -> dict:
        if not base_logs_dir.exists():
            return {"runs": []}
        runs = []
        for fp in sorted(base_logs_dir.glob("*.jsonl"), reverse=True):
            events = _load_events(fp)
            run_id = fp.stem
            total_events = len(events)
            simulations = sorted(
                {
                    f"{event.get('task_id')}#{event.get('trial')}"
                    for event in events
                    if event.get("task_id") is not None and event.get("trial") is not None
                },
                key=lambda item: (
                    task_id_sort_key(item.rsplit("#", 1)[0]),
                    _trial_sort_key(item.rsplit("#", 1)[1]),
                ),
            )
            runs.append(
                {
                    "run_id": run_id,
                    "file_name": fp.name,
                    "total_events": total_events,
                    "simulations": simulations,
                }
            )
        return {"runs": runs}

    @app.get("/api/events")
    def get_events(
        run_id: str = Query(...),
        task_id: Optional[str] = Query(None),
        trial: Optional[int] = Query(None),
        event_type: Optional[str] = Query(None),
        q: Optional[str] = Query(None),
        limit: int = Query(500, ge=1, le=5000),
    ) -> dict:
        file_path = base_logs_dir / f"{run_id}.jsonl"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"run log not found: {run_id}")

        events = _load_events(file_path)
        filtered = []
        for event in events:
            if task_id is not None and event.get("task_id") != task_id:
                continue
            if trial is not None and event.get("trial") != trial:
                continue
            if event_type is not None and event.get("event_type") != event_type:
                continue
            if q is not None and q.strip():
                raw = json.dumps(event, ensure_ascii=False)
                if q.strip().lower() not in raw.lower():
                    continue
            filtered.append(event)

        return {
            "run_id": run_id,
            "count": len(filtered),
            "events": filtered[:limit],
            "truncated": len(filtered) > limit,
        }

    @app.get("/api/simulations")
    def list_simulation_files() -> dict:
        d = _simulations_dir()
        if not d.exists():
            return {"files": []}
        files = []
        for fp in sorted(d.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            st = fp.stat()
            rel = fp.relative_to(d).as_posix()
            files.append(
                {
                    "name": rel,
                    "path": rel,
                    "basename": fp.name,
                    "dir": fp.parent.relative_to(d).as_posix()
                    if fp.parent != d
                    else "",
                    "mtime": st.st_mtime,
                    "size": st.st_size,
                }
            )
        return {"files": files}

    @app.get("/api/simulation-runs")
    def simulation_runs(
        file: str = Query(..., description="simulations 目录下的 json 相对路径"),
        offset: int = Query(0, ge=0),
        limit: Optional[int] = Query(None, ge=1, le=5000),
        reward_filter: Optional[str] = Query(None, pattern="^(non_full)$"),
    ) -> dict:
        path = _resolve_simulation_file(file)
        results = Results.model_validate_json(path.read_text(encoding="utf-8"))
        sorted_rows = _sorted_simulation_rows(results)
        unfiltered_count = len(sorted_rows)
        if reward_filter == "non_full":
            sorted_rows = [
                (original_index, sim)
                for original_index, sim in sorted_rows
                if _is_non_full_reward(sim)
            ]
        visible_rows = sorted_rows[offset : offset + limit] if limit is not None else sorted_rows
        runs = []
        for display_index, (original_index, sim) in enumerate(visible_rows, start=offset):
            runs.append(
                {
                    "display_index": display_index,
                    "index": original_index,
                    "original_index": original_index,
                    **simulation_run_summary(sim),
                }
            )
        return {
            "file": file,
            "task_count": len(results.tasks),
            "simulation_count": len(results.simulations),
            "total_count": len(sorted_rows),
            "unfiltered_count": unfiltered_count,
            "reward_filter": reward_filter,
            "offset": offset,
            "limit": limit,
            "runs": runs,
        }

    @app.get("/api/simulation-timeline")
    def simulation_timeline(
        file: str = Query(..., description="simulations 目录下的 json 相对路径"),
        sim_index: int = Query(0, ge=0, description="results.simulations 中的下标"),
        include_raw: bool = Query(True, description="是否在每条 assistant/user 中包含 raw_data"),
    ) -> dict:
        path = _resolve_simulation_file(file)
        results = Results.model_validate_json(path.read_text(encoding="utf-8"))
        if sim_index >= len(results.simulations):
            raise HTTPException(
                status_code=400,
                detail=f"sim_index out of range: {sim_index} (have {len(results.simulations)} simulations)",
            )
        sim = results.simulations[sim_index]
        timeline = build_timeline_from_simulation(sim, results)
        if not include_raw:
            for row in timeline:
                if row.get("kind") in ("assistant", "user"):
                    row.pop("raw_data", None)
        return {
            "file": file,
            "sim_index": sim_index,
            "summary": simulation_run_summary(sim),
            "evaluation_result": sim.reward_info.model_dump(mode="json")
            if sim.reward_info is not None
            else None,
            "user_simulator_profile": build_user_simulator_profile(
                results, sim.task_id
            ),
            "timeline": timeline,
        }

    @app.get("/api/simulation-raw-json")
    def simulation_raw_json(
        file: str = Query(...),
        sim_index: int = Query(0, ge=0),
        section: str = Query(
            "messages",
            description="messages | full — full 为整份 Results JSON（可能很大）",
        ),
    ) -> dict:
        path = _resolve_simulation_file(file)
        raw_text = path.read_text(encoding="utf-8")
        if section == "full":
            return {
                "file": file,
                "format": "json",
                "text": format_json_for_display(json.loads(raw_text)),
            }
        results = Results.model_validate_json(raw_text)
        if sim_index >= len(results.simulations):
            raise HTTPException(status_code=400, detail="sim_index out of range")
        sim = results.simulations[sim_index]
        return {
            "file": file,
            "sim_index": sim_index,
            "format": "json",
            "text": format_json_for_display(
                [m.model_dump(mode="json") for m in sim.messages]
            ),
        }

    @app.get("/api/simulation-tools")
    def simulation_tools(
        file: str = Query(..., description="simulations 目录下的 json 相对路径"),
        sim_index: int = Query(0, ge=0),
    ) -> dict:
        path = _resolve_simulation_file(file)
        results = Results.model_validate_json(path.read_text(encoding="utf-8"))
        sim, task = _resolve_task_from_simulation(results, sim_index)
        env = _build_environment_for_task(task)
        tools = []
        for t in env.get_tools():
            tools.append(
                {
                    "name": t.name,
                    "short_desc": t.short_desc,
                    "long_desc": t.long_desc,
                    "openai_schema": t.openai_schema,
                    "params_schema": t.params.model_json_schema(),
                    "returns_schema": t.returns.model_json_schema(),
                    "raises": t.raises,
                    "examples": t.examples,
                }
            )
        tools.sort(key=lambda x: x["name"])
        return {
            "file": file,
            "sim_index": sim_index,
            "task_id": sim.task_id,
            "domain": task.domain,
            "note": "工具调用基于该任务的初始 environment 状态，不会自动回放到某一轮对话后的中间状态。",
            "tools": tools,
        }

    @app.post("/api/simulation-tool-invoke")
    def simulation_tool_invoke(req: ToolInvokeRequest) -> dict:
        path = _resolve_simulation_file(req.file)
        results = Results.model_validate_json(path.read_text(encoding="utf-8"))
        sim, task = _resolve_task_from_simulation(results, req.sim_index)
        env = _build_environment_for_task(task)
        tool_msg = env.get_response(
            ToolCall(
                id=f"debug_{uuid.uuid4().hex[:12]}",
                name=req.tool_name,
                arguments=req.arguments or {},
                requestor="assistant",
            )
        )
        return {
            "file": req.file,
            "sim_index": req.sim_index,
            "task_id": sim.task_id,
            "domain": task.domain,
            "tool_message": tool_msg.model_dump(mode="json"),
        }

    return app
