import math
import re
from datetime import datetime
from typing import Optional

import pandas as pd
from loguru import logger
from pydantic import BaseModel

from vita.data_model.simulation import Results


def is_successful(reward: float) -> bool:
    """
    Check if the reward is successful.
    """
    return reward == 1.0


class AgentMetrics(BaseModel):
    avg_reward: float
    pass_hat_ks: dict[int, float]
    pass_at_n: Optional[dict[int, float]] = None
    average_at_n: Optional[dict[int, float]] = None
    avg_agent_cost: float
    avg_reward_breakdown: Optional[dict] = None
    total_duration: Optional[float] = None
    all_types_metrics: Optional[dict] = None

    def as_dict(self) -> dict:
        data = {
            "avg_reward": self.avg_reward,
            "avg_agent_cost": self.avg_agent_cost,
        }
        for k, v in self.pass_hat_ks.items():
            data[f"pass_hat_{k}"] = v
        if self.pass_at_n:
            for n, v in self.pass_at_n.items():
                data[f"pass_at_{n}"] = v
        if self.average_at_n:
            for n, v in self.average_at_n.items():
                data[f"average_at_{n}"] = v
        if self.avg_reward_breakdown:
            data["avg_reward_breakdown"] = self.avg_reward_breakdown
        if self.total_duration:
            data["total_duration"] = self.total_duration
        if self.all_types_metrics:
            data["all_types_metrics"] = self.all_types_metrics
        return data


def pass_hat_k(num_trials: int, success_count: int, k: int) -> float:
    """
    Compute the pass^k metric for the given number of trials, success count, and k.
    from https://arxiv.org/pdf/2406.12045
    Args:
        num_trials: The number of trials.
        success_count: The number of successful trials.
        k: The number of trials to consider.
    Returns:
        The pass^k metric.
    """
    if num_trials < k:
        raise ValueError(f"Number of trials {num_trials} is less than k {k}.")
    return math.comb(success_count, k) / math.comb(num_trials, k)


def pass_at_k(num_trials: int, success_count: int, k: int) -> float:
    """
    Compute the pass@k metric for the given number of trials, success count, and k.
    Based on the formula: pass@k = 1 - (n-c choose k) / (n choose k)
    where n is the number of trials and c is the number of successful trials.
    
    Args:
        num_trials: The number of trials (n).
        success_count: The number of successful trials (c).
        k: The number of trials to consider.
    Returns:
        The pass@k metric.
    """
    if num_trials < k:
        return 0.0
    
    if success_count > num_trials:
        return 0.0
    
    if num_trials - success_count >= k:
        # If we have enough unsuccessful trials to choose k
        return 1.0 - (math.comb(num_trials - success_count, k) / math.comb(num_trials, k))
    else:
        # If we don't have enough unsuccessful trials, pass@k = 1
        return 1.0


def average_at_k(rewards: list[float], k: int) -> float:
    if len(rewards) < k:
        return 0.0
    
    if k == 0:
        return 0.0
    
    return sum(rewards) / len(rewards)


def get_metrics_df(results: Results) -> tuple[pd.DataFrame, int]:
    """
    Convert the results to a dataframe and add a column for success.
    Checks that all simulations have the same number of trials.
    Returns the maximum number of trials that can be used for pass^k metrics.
    """
    df = results.to_df()
    df["success"] = df.reward.apply(is_successful)
    if len(df.info_num_trials.unique()) > 1:
        logger.warning(
            f"All simulations must have the same number of trials. Found {df.info_num_trials.unique()}"
        )
    max_k = df.info_num_trials.max()

    task_ids_counts = [(tid, count) for tid, count in df.task_id.value_counts().items()]
    task_ids_counts.sort(key=lambda x: x[1])
    min_k = task_ids_counts[0][1]
    if min_k < max_k:
        logger.warning(
            f"The minimum number of trials for a task is {min_k}, which is less than the expected number of trials {max_k}. Setting max k to {min_k}."
        )
        max_k = min_k
    return df, max_k


def get_tasks_pass_hat_k(results: Results) -> pd.DataFrame:
    """
    Compute the pass^k for each k from 1 to the maximum number of trials.
    """
    df, max_k = get_metrics_df(results)
    dfs = []
    for k in range(1, max_k + 1):
        res = df.groupby("task_id")["success"].apply(
            lambda df: pass_hat_k(len(df), df.sum(), k)
        )
        res.name = f"pass^{k}"
        dfs.append(res)
    df_pass_hat_k = pd.concat(dfs, axis=1)
    return df_pass_hat_k


def prepare_dfs(results: Results) -> tuple[pd.DataFrame, pd.DataFrame]:
    df, max_k = get_metrics_df(results)
    df_pass_hat_k = get_tasks_pass_hat_k(results)
    return df, df_pass_hat_k


def compute_metrics(results: Results) -> AgentMetrics:
    """
    Compute metrics for the agent.
    - average reward
    - pass^k
    - average reward breakdown
    - total duration
    """
    df, df_pass_hat_k = prepare_dfs(results)
    avg_reward = df.reward.mean()
    pass_hat_ks = {}
    for column in df_pass_hat_k.columns:
        if match := re.match(r"pass\^(\d+)", column):
            k = int(match.group(1))
            pass_hat_ks[k] = df_pass_hat_k[column].mean()

    # Calculate pass@k and average@k based on the mathematical formula from the paper
    # pass@k = 1 - E_task [ (n - c choose k) / (n choose k) ]
    pass_at_n = {}
    average_at_n = {}
    num_trials = results.info.num_trials
    
    # Group by task_id to calculate pass@k and average@k
    task_groups = df.groupby("task_id")
    for k in range(1, num_trials + 1):
        pass_at_k_values = []
        average_at_k_values = []
        
        for task_id, task_df in task_groups:
            if len(task_df) >= k:
                n = len(task_df)  # number of trials for this task
                c = task_df["success"].sum()  # number of successful trials
                
                # Calculate pass@k using the helper function
                pass_at_k_value = pass_at_k(n, c, k)
                pass_at_k_values.append(pass_at_k_value)
                
                # Calculate average@k using the helper function
                rewards = task_df["reward"].tolist()
                average_at_k_value = average_at_k(rewards, k)
                average_at_k_values.append(average_at_k_value)
        
        if pass_at_k_values:
            pass_at_n[k] = sum(pass_at_k_values) / len(pass_at_k_values)
        if average_at_k_values:
            average_at_n[k] = sum(average_at_k_values) / len(average_at_k_values)

    avg_agent_cost = df.agent_cost.mean()
    
    # Calculate average reward breakdown
    avg_reward_breakdown = {}
    reward_breakdown_counts = {}
    for sim in results.simulations:
        if sim.reward_info and sim.reward_info.reward_breakdown:
            for reward_type, value in sim.reward_info.reward_breakdown.items():
                if reward_type not in avg_reward_breakdown:
                    avg_reward_breakdown[reward_type] = 0.0
                    reward_breakdown_counts[reward_type] = 0
                avg_reward_breakdown[reward_type] += value
                reward_breakdown_counts[reward_type] += 1

    # Convert to averages
    for reward_type in avg_reward_breakdown:
        if reward_breakdown_counts[reward_type] > 0:
            avg_reward_breakdown[reward_type] /= reward_breakdown_counts[reward_type]

    # Calculate total duration as the time difference between the latest end_time and earliest start_time
    if results.simulations:
        # Parse start_time and end_time strings to datetime objects
        start_times = []
        end_times = []
        for sim in results.simulations:
            try:
                start_times.append(datetime.strptime(sim.start_time, "%Y%m%d_%H%M%S"))
                end_times.append(datetime.strptime(sim.end_time, "%Y%m%d_%H%M%S"))
            except ValueError:
                # Fallback to original duration calculation if time parsing fails
                logger.warning(f"Failed to parse time format for simulation {sim.id}, using original duration calculation")
                total_duration = sum(sim.duration for sim in results.simulations)
                break
        else:
            # If all time parsing succeeded, calculate the time difference
            earliest_start = min(start_times)
            latest_end = max(end_times)
            total_duration = (latest_end - earliest_start).total_seconds()
    else:
        total_duration = 0.0

    # Check if we have all_types evaluation results
    all_types_metrics = {}
    if len(results.simulations) > 0 and results.simulations[0].reward_info and results.simulations[0].reward_info.info:
        first_sim = results.simulations[0]
        if first_sim.reward_info.info.get("evaluation_methods") == ["trajectory"]:
            # We have all_types evaluation, compute metrics for each method

            all_types_metrics = {}
            
            # Compute trajectory metrics
            trajectory_rewards = []
            trajectory_task_ids = []
            for sim in results.simulations:
                if sim.reward_info and sim.reward_info.info and "trajectory_evaluation" in sim.reward_info.info:
                    trajectory_rewards.append(sim.reward_info.info["trajectory_evaluation"]["reward"])
                    trajectory_task_ids.append(sim.task_id)
            
            if trajectory_rewards:
                trajectory_df = pd.DataFrame({
                    "reward": trajectory_rewards,
                    "task_id": trajectory_task_ids
                })
                trajectory_df["success"] = trajectory_df.reward.apply(is_successful)
                
                # Calculate pass_hat_ks for trajectory evaluation using the same logic
                trajectory_pass_hat_ks = {}
                # Get the minimum number of trials across all tasks
                task_counts = trajectory_df.groupby("task_id").size()
                min_trials = task_counts.min()
                max_k = min_trials
                
                for k in range(1, max_k + 1):
                    if min_trials >= k:
                        # Group by task_id and calculate pass^k for each task, then take mean
                        task_pass_ks = trajectory_df.groupby("task_id")["success"].apply(
                            lambda df: pass_hat_k(len(df), df.sum(), k)
                        )
                        trajectory_pass_hat_ks[k] = task_pass_ks.mean()
                
                # Compute trajectory reward breakdown
                trajectory_breakdown = {}
                trajectory_breakdown_counts = {}
                for sim in results.simulations:
                    if sim.reward_info and sim.reward_info.info and "trajectory_evaluation" in sim.reward_info.info:
                        eval_info = sim.reward_info.info["trajectory_evaluation"]
                        if "reward_breakdown" in eval_info and eval_info["reward_breakdown"] is not None:
                            for reward_type, value in eval_info["reward_breakdown"].items():
                                if reward_type not in trajectory_breakdown:
                                    trajectory_breakdown[reward_type] = 0.0
                                    trajectory_breakdown_counts[reward_type] = 0
                                trajectory_breakdown[reward_type] += value
                                trajectory_breakdown_counts[reward_type] += 1

                # Convert to averages
                for reward_type in trajectory_breakdown:
                    if trajectory_breakdown_counts[reward_type] > 0:
                        trajectory_breakdown[reward_type] /= trajectory_breakdown_counts[reward_type]

                # Calculate pass@k and average@k for trajectory evaluation using the same formula
                # pass@k = 1 - E_task [ (n - c choose k) / (n choose k) ]
                trajectory_pass_at_n = {}
                trajectory_average_at_n = {}
                
                trajectory_task_groups = trajectory_df.groupby("task_id")
                for k in range(1, num_trials + 1):
                    trajectory_pass_at_k_values = []
                    trajectory_average_at_k_values = []
                    
                    for task_id, task_df in trajectory_task_groups:
                        if len(task_df) >= k:
                            n = len(task_df)  # number of trials for this task
                            c = task_df["success"].sum()  # number of successful trials
                            
                            # Calculate pass@k using the helper function
                            trajectory_pass_at_k_value = pass_at_k(n, c, k)
                            trajectory_pass_at_k_values.append(trajectory_pass_at_k_value)
                            
                            # Calculate average@k using the helper function
                            rewards = task_df["reward"].tolist()
                            trajectory_average_at_k_value = average_at_k(rewards, k)
                            trajectory_average_at_k_values.append(trajectory_average_at_k_value)
                    
                    if trajectory_pass_at_k_values:
                        trajectory_pass_at_n[k] = sum(trajectory_pass_at_k_values) / len(trajectory_pass_at_k_values)
                    if trajectory_average_at_k_values:
                        trajectory_average_at_n[k] = sum(trajectory_average_at_k_values) / len(trajectory_average_at_k_values)

                all_types_metrics["trajectory"] = {
                    "avg_reward": trajectory_df.reward.mean(),
                    "pass_hat_ks": trajectory_pass_hat_ks,
                    "pass_at_n": trajectory_pass_at_n,
                    "average_at_n": trajectory_average_at_n,
                    "avg_reward_breakdown": trajectory_breakdown if trajectory_breakdown else None,
                }


    return AgentMetrics(
        avg_reward=avg_reward,
        pass_hat_ks=pass_hat_ks,
        pass_at_n=pass_at_n,
        average_at_n=average_at_n,
        avg_agent_cost=avg_agent_cost,
        avg_reward_breakdown=avg_reward_breakdown if avg_reward_breakdown else None,
        total_duration=total_duration,
        all_types_metrics=all_types_metrics if all_types_metrics else None,
    )


def display_metrics(metrics: AgentMetrics) -> None:
    print(f"🏆 Average reward: {metrics.avg_reward}")
    print("📈 Pass^k")
    for k, pass_hat_k in metrics.pass_hat_ks.items():
        print(f"  k={k}: {pass_hat_k}")
    
    # Display pass@k and average@k metrics
    if metrics.pass_at_n:
        print("📈 Pass@K")
        for k, pass_at_k_value in metrics.pass_at_n.items():
            print(f"  k={k}: {pass_at_k_value:.4f}")
    
    if metrics.average_at_n:
        print("📈 Average@K")
        for k, average_at_k_value in metrics.average_at_n.items():
            print(f"  k={k}: {average_at_k_value:.4f}")
    
    print(f"💰 Average agent cost: {metrics.avg_agent_cost}")
    
    # Display reward breakdown averages
    if metrics.avg_reward_breakdown:
        print("\n📊 Average Reward Breakdown:")
        for reward_type, avg_value in metrics.avg_reward_breakdown.items():
            print(f"  {reward_type}: {avg_value:.4f}")

    # Display total duration
    if metrics.total_duration:
        print(f"\n⏱️ Total Duration: {metrics.total_duration/60:.2f}min")

    # Display all_types metrics if available
    if metrics.all_types_metrics:
        print("\n🔄 All Evaluation Types Results:")
        for eval_type, eval_metrics in metrics.all_types_metrics.items():
            print(f"  {eval_type.upper()}:")
            if "avg_reward" in eval_metrics:
                print(f"    Average reward: {eval_metrics['avg_reward']:.4f}")

            # Display reward breakdown for this evaluation type
            if eval_metrics.get("avg_reward_breakdown"):
                print("    Reward Breakdown:")
                for reward_type, avg_value in eval_metrics["avg_reward_breakdown"].items():
                    print(f"      {reward_type}: {avg_value:.4f}")

            if "pass_hat_ks" in eval_metrics:
                print("    Pass^k:")
                for k, pass_hat_k in eval_metrics["pass_hat_ks"].items():
                    print(f"      k={k}: {pass_hat_k:.4f}")

            if "pass_at_n" in eval_metrics:
                print("    Pass@K:")
                for k, pass_at_k_value in eval_metrics["pass_at_n"].items():
                    print(f"      k={k}: {pass_at_k_value:.4f}")

            if "average_at_n" in eval_metrics:
                print("    Average@K:")
                for k, average_at_k_value in eval_metrics["average_at_n"].items():
                    print(f"      k={k}: {average_at_k_value:.4f}")


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=str, required=True)
    args = parser.parse_args()
    results = Results.load(Path(args.results))
    metrics = compute_metrics(results)
    display_metrics(metrics)
