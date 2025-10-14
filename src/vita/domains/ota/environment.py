import json
from typing import Optional

from vita.data_model.tasks import Task
from vita.domains.ota.data_model import OTADB
from vita.domains.ota.tools import OTATools
from vita.utils.utils import get_task_file_path
from vita.environment.environment import Environment


def get_environment(
        db: Optional[OTADB] = None,
        language: str = None,
) -> Environment:
    # 设置全局语言配置
    if language is not None:
        from vita.utils.schema_utils import set_global_language
        set_global_language(language)
    
    if db is None:
        db = {}

    db_dict = {k: v for k, v in db.items() if
               k in ["orders", "hotels", "attractions", "flights", "trains", "time", "user_id", "weather", "location",
                     "user_historical_behaviors"]}
    if "hotels" not in db_dict:
        db_dict["hotels"] = {}
    if "attractions" not in db_dict:
        db_dict["attractions"] = {}
    if "flights" not in db_dict:
        db_dict["flights"] = {}
    if "trains" not in db_dict:
        db_dict["trains"] = {}
    if "orders" not in db_dict:
        db_dict["orders"] = {}

    db = OTADB.model_validate(db_dict)
    tools = OTATools(db)
    from vita.environment.environment import get_agent_policy
    return Environment(
        domain_name="ota",
        policy=get_agent_policy(language),
        tools=tools,
    )


def get_tasks(language: str = None) -> list[Task]:
    task_path = get_task_file_path("ota", language)
    with open(task_path, "r") as fp:
        tasks = json.load(fp)
    return [Task.model_validate(task) for task in tasks]
