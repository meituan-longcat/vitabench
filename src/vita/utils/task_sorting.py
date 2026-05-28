import re
from typing import Any


def task_id_sort_key(task_id: Any) -> tuple:
    """Natural ascending key; digit-leading ids sort before letter-leading (e.g. 10807012 before A0812003)."""
    s = str(task_id)
    if s[:1].isdigit():
        leading = 0
    elif s[:1].isalpha():
        leading = 1
    else:
        leading = 2
    parts = re.split(r"(\d+)", s)
    key = []
    for part in parts:
        if not part:
            continue
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part.lower()))
    return (leading,) + tuple(key)


def simulation_sort_key(simulation: Any) -> tuple:
    trial = getattr(simulation, "trial", None)
    seed = getattr(simulation, "seed", None)
    return (
        task_id_sort_key(getattr(simulation, "task_id", "")),
        trial if trial is not None else -1,
        seed if seed is not None else -1,
    )


def task_sort_key(task: Any) -> tuple:
    return (task_id_sort_key(getattr(task, "id", "")),)
