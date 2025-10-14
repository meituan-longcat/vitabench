from vita.data_model.simulation import RewardInfo, EvaluationType, SimulationRun, TerminationReason
from vita.data_model.tasks import Task
from vita.evaluator.evaluator_traj import TrajectoryEvaluator


def evaluate_simulation(
    simulation: SimulationRun,
    task: Task,
    evaluation_type: EvaluationType,
    domain: str,
    llm_evaluator: str = None,
    llm_args_evaluator: dict = None,
    language: str = None,
) -> RewardInfo:
    """
    Evaluate the simulation based on the evaluation type.
    """
    if simulation.termination_reason in {
        TerminationReason.TOO_MANY_ERRORS,
        TerminationReason.MAX_STEPS,
        TerminationReason.INVALID_AGENT_MESSAGE,
    }:
        return RewardInfo(
            reward=0.0,
            info={
                "note": f"Simulation terminated prematurely. Termination reason: {simulation.termination_reason}"
            },
        )
    if task.evaluation_criteria is None:
        return RewardInfo(
            reward=1.0,
            info={"note": "No evaluation criteria"},
        )
    if evaluation_type == "trajectory":
        reward_info = TrajectoryEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
            final_state=simulation.states,
            llm_evaluator=llm_evaluator,
            llm_args_evaluator=llm_args_evaluator,
            language=language,
        )
    elif evaluation_type == "trajectory_full_traj_rubric":
        reward_info = TrajectoryEvaluator.calculate_reward_full_traj_rubric(
            task=task,
            full_trajectory=simulation.messages,
            final_state=simulation.states,
            llm_evaluator=llm_evaluator,
            llm_args_evaluator=llm_args_evaluator,
            language=language,
        )
    elif evaluation_type == "trajectory_sliding_wo_rubric":
        reward_info = TrajectoryEvaluator.calculate_reward_sliding_wo_rubric(
            task=task,
            full_trajectory=simulation.messages,
            final_state=simulation.states,
            llm_evaluator=llm_evaluator,
            llm_args_evaluator=llm_args_evaluator,
            language=language,
        )
    elif evaluation_type == "trajectory_full_traj_wo_rubric":
        reward_info = TrajectoryEvaluator.calculate_reward_full_traj_wo_rubric(
            task=task,
            full_trajectory=simulation.messages,
            final_state=simulation.states,
            llm_evaluator=llm_evaluator,
            llm_args_evaluator=llm_args_evaluator,
            language=language,
        )
    else:
        raise ValueError(f"Unknown evaluation type: {evaluation_type}")
    return reward_info
