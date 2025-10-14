import json
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Optional, Any, Literal, Dict

import pandas as pd
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from vita.config import (
    DEFAULT_LLM_AGENT,
    DEFAULT_LLM_USER,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MAX_ERRORS,
    DEFAULT_MAX_STEPS,
    DEFAULT_EVALUATION_TYPE,
    DEFAULT_NUM_TRIALS,
    DEFAULT_SAVE_TO,
    DEFAULT_SEED,
    DEFAULT_LLM_EVALUATOR,
    DEFAULT_LANGUAGE,
    models
)
from vita.data_model.message import Message
from vita.data_model.tasks import RewardType, Task
from vita.environment.environment import EnvironmentInfo
from vita.utils.utils import get_now


EvaluationType = Literal[
    "trajectory",
    "trajectory_full_traj_rubric",
    "trajectory_sliding_wo_rubric",
    "trajectory_full_traj_wo_rubric"
]


class RunConfig(BaseModel):
    domain: Annotated[
        str,
        Field(
            description="The domain to run the simulation on",
            default="ota",
        ),
    ]
    task_set_name: Annotated[
        Optional[str],
        Field(
            description="The task set to run the simulation on. If not provided, will load default task set for the domain.",
            default=None,
        ),
    ]
    task_ids: Annotated[
        Optional[list[str]],
        Field(
            description="The task IDs to run the simulation on",
            default=None,
        ),
    ]
    num_tasks: Annotated[
        Optional[int],
        Field(
            description="The number of tasks to run the simulation on",
            default=None,
        ),
    ]
    is_remote: Annotated[
        bool,
        Field(
            description="Whether to run the simulation remotely",
            default=False,
        ),
    ]
    agent: Annotated[
        str,
        Field(
            description="The type of agent to run the simulation on",
            default="llm_agent",
        ),
    ]
    llm_agent: Annotated[
        str,
        Field(
            description="The model to use for the agent",
            default=DEFAULT_LLM_AGENT,
        ),
    ]
    llm_args_agent: Annotated[
        dict,
        Field(
            description="The arguments to pass to the LLM for the agent",
            default_factory=lambda: deepcopy(models[DEFAULT_LLM_AGENT]),
        ),
    ]
    user: Annotated[
        str,
        Field(
            description="The type of user to run the simulation on",
            default="user_simulator",
        ),
    ]
    llm_user: Annotated[
        str,
        Field(
            description="The model to use for the user",
            default=DEFAULT_LLM_USER,
        ),
    ]
    llm_args_user: Annotated[
        dict,
        Field(
            description="The arguments to pass to the LLM for the user",
            default_factory=lambda: deepcopy(models[DEFAULT_LLM_USER]),
        ),
    ]
    num_trials: Annotated[
        int,
        Field(
            description="The number of trials to run the simulation on",
            default=DEFAULT_NUM_TRIALS,
        ),
    ]
    max_steps: Annotated[
        int,
        Field(
            description="The maximum number of steps to run the simulation",
            default=DEFAULT_MAX_STEPS,
        ),
    ]
    evaluation_type: Annotated[
        EvaluationType,
        Field(
            description="The type of evaluation to use. Choices: trajectory, trajectory_full_traj_rubric, trajectory_sliding_wo_rubric, trajectory_full_traj_wo_rubric.",
            default=DEFAULT_EVALUATION_TYPE,
        ),
    ]
    max_errors: Annotated[
        int,
        Field(
            description="The maximum number of tool errors allowed in a row in the simulation",
            default=DEFAULT_MAX_ERRORS,
        ),
    ]
    save_to: Annotated[
        Optional[str],
        Field(
            description="The path to json file where to save the simulation results",
            default=DEFAULT_SAVE_TO,
        ),
    ]
    max_concurrency: Annotated[
        int,
        Field(
            description="The maximum number of concurrent simulations to run",
            default=DEFAULT_MAX_CONCURRENCY,
        ),
    ]
    seed: Annotated[
        Optional[int],
        Field(
            description="The seed to use for the simulation",
            default=DEFAULT_SEED,
        ),
    ]
    log_level: Annotated[
        Optional[str],
        Field(
            description="The log level to use for the simulation",
            default=DEFAULT_LOG_LEVEL,
        ),
    ]
    re_evaluate_file: Annotated[
        Optional[str],
        Field(
            description="Path to simulation file for re-evaluation mode",
            default=None,
        ),
    ]
    csv_output_file: Annotated[
        Optional[str],
        Field(
            description="Path to csv output file for result analysis",
            default=None,
        ),
    ]
    enable_think: Annotated[
        bool,
        Field(
            description="Whether to enable think step for the agent",
            default=False,
        ),
    ]
    language: Annotated[
        str,
        Field(
            description="The language to use for prompts and tasks. Choices: chinese, english",
            default=DEFAULT_LANGUAGE,
        ),
    ]
    llm_evaluator: Annotated[
        str,
        Field(
            description="The LLM to use for evaluation",
            default=DEFAULT_LLM_EVALUATOR,
        ),
    ]
    llm_args_evaluator: Annotated[
        dict,
        Field(
            description="The arguments to pass to the LLM for evaluation",
            default_factory=lambda: deepcopy(models[DEFAULT_LLM_EVALUATOR]),
        ),
    ]
    re_run: Annotated[
        bool,
        Field(
            description="Whether to re-run tasks specified by task_ids. If used with re_evaluate_file, will re-run specified tasks and then re-evaluate all tasks together.",
            default=False,
        ),
    ]

    def validate(self) -> None:
        """
        Validate the run config
        """
        # Validate re_run parameter usage
        if self.re_run:
            if not self.re_evaluate_file:
                raise ValueError("--re-run can only be used with --re-evaluate-file")
            if not self.task_ids:
                raise ValueError("--re-run requires --task-ids to specify which tasks to re-run")


class NLRubricCheck(BaseModel):
    """
    A natural language assertion.
    """

    nl_rubric: Optional[str] = None
    met: bool
    justification: str

class RewardInfo(BaseModel):
    """
    The reward received by the agent.
    """

    reward: Annotated[float, Field(description="The reward received by the agent.")]
    nl_rubrics: Annotated[
        Optional[list[NLRubricCheck]],
        Field(description="The natural language assertions.", default=None),
    ]
    reward_breakdown: Annotated[
        Optional[dict[RewardType, float]],
        Field(
            description="The breakdown of the reward.",
            default=None,
        ),
    ]
    info: Annotated[
        Optional[dict],
        Field(description="Additional information about the reward.", default=None),
    ]
    window_evaluations: Annotated[
        Optional[list[dict]],
        Field(description="Detailed evaluation information for each sliding window.", default=None),
    ]


class AgentInfo(BaseModel):
    """
    Agent information.
    """

    implementation: str = Field(description="The type of agent.")
    llm: Optional[str] = Field(description="The LLM used by the agent.", default=None)
    llm_args: Optional[dict] = Field(
        description="The arguments to pass to the LLM for the agent.", default=None
    )


class UserInfo(BaseModel):
    """
    User information.
    """

    implementation: str = Field(description="The type of user.")
    llm: Optional[str] = Field(description="The LLM used by the user.", default=None)
    llm_args: Optional[dict] = Field(
        description="The arguments to pass to the LLM for the user.", default=None
    )
    global_simulation_guidelines: Optional[str] = Field(
        description="The global simulation guidelines for the user.", default=None
    )


class Info(BaseModel):
    """Information about the simulator."""

    git_commit: str = Field(description="The git commit hash.")
    num_trials: int = Field(description="The number of trials.")
    max_steps: int = Field(description="The maximum number of steps.")
    max_errors: int = Field(description="The maximum number of errors.")
    user_info: UserInfo = Field(description="User information.")
    agent_info: AgentInfo = Field(description="Agent information.")
    environment_info: EnvironmentInfo = Field(description="Environment information.")
    seed: Optional[int] = Field(
        description="The seed used for the simulation.", default=None
    )


class TerminationReason(str, Enum):
    USER_STOP = "user_stop"
    AGENT_STOP = "agent_stop"
    MAX_STEPS = "max_steps"
    TOO_MANY_ERRORS = "too_many_errors"
    INVALID_AGENT_MESSAGE = "invalid_agent_message"


class SimulationRun(BaseModel):
    """
    Simulation run for the given task.
    """

    id: str = Field(description="The unique identifier for the simulation run.")
    task_id: str = Field(description="The unique identifier for the task.")
    timestamp: str = Field(
        description="The timestamp of the simulation.", default_factory=get_now
    )
    start_time: str = Field(description="The start time of the simulation.")
    end_time: str = Field(description="The end time of the simulation.")
    duration: float = Field(description="The duration of the simulation.")
    termination_reason: TerminationReason = Field(
        description="The reason for the termination of the simulation."
    )
    agent_cost: Optional[float] = Field(
        description="The cost of the agent.", default=None
    )
    user_cost: Optional[float] = Field(
        description="The cost of the user.", default=None
    )
    reward_info: Optional[RewardInfo] = Field(
        description="The reward received by the agent.", default=None
    )
    messages: list[Message] = Field(
        description="The messages exchanged between the user, agent and environment."
    )
    states: Dict[str, Any] = Field(
        description="The final state, including old states and new states", default={"old_states": [], "new_states": []}
    )
    trial: Optional[int] = Field(description="Trial number", default=None)
    seed: Optional[int] = Field(
        description="Seed used for the simulation.", default=None
    )
    


class Results(BaseModel):
    """
    Run results
    """

    timestamp: Optional[str] = Field(
        description="The timestamp of the simulation.", default_factory=get_now
    )
    info: Info = Field(description="Information.")
    tasks: list[Task] = Field(description="The list of tasks.")
    simulations: list[SimulationRun] = Field(description="The list of simulations.")

    @classmethod
    def load(cls, path: Path) -> "Results":
        with open(path, "r") as f:
            return cls.model_validate_json(f.read())

    def save(self, path: Path) -> None:
        """
        Save the results to a file.
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    def to_df(self) -> pd.DataFrame:
        """
        Convert a Results object to a pandas DataFrame.
        """
        def clean_value_for_dataframe(value):
            """Clean a value to ensure it's compatible with pandas DataFrame"""
            if value is None:
                return None
            try:
                # Try to serialize to check if it's compatible
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                # If not serializable, convert to string
                if hasattr(value, 'tolist'):
                    try:
                        return value.tolist()
                    except:
                        return str(value)
                else:
                    return str(value)

        rows = []
        for sim in self.simulations:
            row = {
                "simulation_id": sim.id,
                "task_id": sim.task_id,
                "trial": sim.trial,
                "seed": sim.seed,
                "reward": sim.reward_info.reward,
                "agent_cost": sim.agent_cost,
                "user_cost": sim.user_cost,
                "termination_reason": sim.termination_reason,
                "duration": sim.duration,
                "num_messages": len(sim.messages),
                "info_git_commit": self.info.git_commit,
                "info_seed": self.info.seed,
                "info_num_trials": self.info.num_trials,
                "info_max_steps": self.info.max_steps,
                "info_max_errors": self.info.max_errors,
                "info_domain": self.info.environment_info.domain_name,
                "info_user_implementation": self.info.user_info.implementation,
                "info_user_llm": self.info.user_info.llm,
                "info_user_llm_args": clean_value_for_dataframe(self.info.user_info.llm_args),
                "info_agent_implementation": self.info.agent_info.implementation,
                "info_agent_llm": self.info.agent_info.llm,
                "info_agent_llm_args": clean_value_for_dataframe(self.info.agent_info.llm_args),
            }
            rows.append(row)
        return pd.DataFrame(rows)
