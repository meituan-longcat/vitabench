import json
from typing import Optional

from vita.data_model.tasks import Task
from vita.domains.instore.data_model import InStoreDB
from vita.domains.instore.tools import InStoreTools
from vita.utils.utils import get_task_file_path
from vita.environment.environment import Environment


def get_environment(
        db: Optional[InStoreDB] = None,
        language: str = None,
) -> Environment:
    # 设置全局语言配置
    if language is not None:
        from vita.utils.schema_utils import set_global_language
        set_global_language(language)
    
    if db is None:
        db = {}

    db_dict = {k: v for k, v in db.items() if
               k in ["shops", "orders", "reservations", "books", "time", "user_id", "weather", "location",
                     "user_historical_behaviors"]}
    if "shops" not in db_dict:
        db_dict["shops"] = {}
    if "books" not in db_dict:
        db_dict["books"] = {}
    if "reservations" not in db_dict:
        db_dict["reservations"] = {}
    if "orders" not in db_dict:
        db_dict["orders"] = {}

    db = InStoreDB.model_validate(db_dict)
    tools = InStoreTools(db)
    from vita.environment.environment import get_agent_policy
    return Environment(
        domain_name="instore",
        policy=get_agent_policy(language),
        tools=tools,
    )


def get_tasks(language: str = None) -> list[Task]:
    task_path = get_task_file_path("instore", language)
    with open(task_path, "r") as fp:
        tasks = json.load(fp)
    return [Task.model_validate(task) for task in tasks]
