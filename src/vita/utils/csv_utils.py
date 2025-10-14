import pandas as pd
from pathlib import Path


def save_results_to_csv(results, csv_path: str, config, metrics):
    """Save simulation results to CSV file in append mode - one row per run"""
    # Create a summary row for this run
    summary_row = create_run_summary(results, metrics, config)

    # Ensure the directory exists
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists to determine if we need to write headers
    file_exists = csv_path.exists()

    if file_exists:
        # Read existing CSV to get column structure and align fields
        try:
            existing_df = pd.read_csv(csv_path)
            existing_columns = existing_df.columns.tolist()
            if len(existing_columns) <= len(summary_row.keys()):
                judge = True
            else:
                judge = False

            # Ensure new data has all existing columns, fill missing ones with None
            for col in existing_columns:
                if col not in summary_row:
                    summary_row[col] = None

            # Check if we have new columns or if column order has changed
            new_columns = set(summary_row.keys()) - set(existing_columns)
            current_column_order = list(summary_row.keys())
            existing_column_order = existing_columns
            
            # Check if we need to rewrite: new columns OR different column order
            if new_columns or current_column_order != existing_column_order:
                if new_columns:
                    print(f"New columns detected: {new_columns}")
                if current_column_order != existing_column_order:
                    print(f"Column order changed from {existing_column_order} to {current_column_order}")
                print("Rewriting CSV with updated column structure...")

                # Read all existing data and add new columns with None values
                existing_data = existing_df.to_dict('records')
                for row in existing_data:
                    for col in new_columns:
                        row[col] = None

                # Add the new row
                existing_data.append(summary_row)
                
                if judge:
                    # Use new data's column order if it has same or more columns
                    final_columns = list(summary_row.keys())
                else:
                    # Use existing column order if it has more columns
                    final_columns = existing_columns
                
                new_df = pd.DataFrame(existing_data)
                
                # Reorder columns according to the selected column structure
                new_df = new_df[final_columns]
                
                new_df.to_csv(csv_path, index=False)
                print(f"Rewrote CSV with {len(new_df)} rows and {len(new_df.columns)} columns")
                return

        except Exception as e:
            print(f"Warning: Could not read existing CSV structure: {e}")

    # Convert summary to DataFrame and append to CSV
    df = pd.DataFrame([summary_row])
    df.to_csv(csv_path, mode='a', header=not file_exists, index=False)

    print(f"Appended 1 run summary to {csv_path}")


def create_run_summary(results, metrics, config):
    """Create a summary row for the entire run"""
    from vita.utils.utils import get_now

    if not results.simulations:
        return {}

    # Get basic run info
    first_sim = results.simulations[0]
    info = results.info

    # Calculate aggregated metrics
    total_simulations = len(results.simulations)
    total_tasks = len(set(sim.task_id for sim in results.simulations))
    total_trials = len(set(sim.trial for sim in results.simulations))

    # Calculate reward statistics
    rewards = [sim.reward_info.reward for sim in results.simulations if sim.reward_info]
    avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
    min_reward = min(rewards) if rewards else 0.0
    max_reward = max(rewards) if rewards else 0.0

    # Calculate cost statistics
    agent_costs = [sim.agent_cost for sim in results.simulations if sim.agent_cost is not None]
    user_costs = [sim.user_cost for sim in results.simulations if sim.user_cost is not None]
    total_agent_cost = sum(agent_costs) if agent_costs else 0.0
    total_user_cost = sum(user_costs) if user_costs else 0.0

    # Calculate duration statistics
    durations = [sim.duration for sim in results.simulations if sim.duration is not None]
    total_duration = sum(durations) if durations else 0.0

    # Count termination reasons
    termination_reasons = {}
    for sim in results.simulations:
        reason = sim.termination_reason.value if sim.termination_reason else "unknown"
        termination_reasons[reason] = termination_reasons.get(reason, 0) + 1

    try:
        # Generate simulation filename
        simulation_filename = config.save_to if config.save_to else config.re_evaluate_file

        # Create summary row
        summary = {
            "run_timestamp": get_now(),
            "run_id": f"{get_now()}_{info.environment_info.domain_name}_{info.agent_info.implementation}_{info.user_info.implementation}{'_think' if config.enable_think else ''}",
            "simulation_filename": simulation_filename,
            "domain": info.environment_info.domain_name,
            "agent_implementation": info.agent_info.implementation,
            "agent_llm": info.agent_info.llm,
            "user_implementation": info.user_info.implementation,
            "user_llm": info.user_info.llm,
            "evaluator_llm": config.llm_evaluator,
            "num_tasks": total_tasks,
            "num_trials": total_trials,
            "total_simulations": total_simulations,
            "avg_reward": round(avg_reward, 4),
            "min_reward": round(min_reward, 4),
            "max_reward": round(max_reward, 4),
            "total_agent_cost": round(total_agent_cost, 4),
            "total_user_cost": round(total_user_cost, 4),
            "total_duration": round(total_duration / 60, 2),
            "termination_reasons": str(termination_reasons),
            "git_commit": info.git_commit,
            "seed": info.seed,
            "max_steps": info.max_steps,
            "max_errors": info.max_errors,
            "max_concurrency": config.max_concurrency,
            "enable_think": config.enable_think,
            "evaluation_type": config.evaluation_type,
        }

        # Add all metrics for each evaluation type together
        if config.evaluation_type == "trajectory":
            # Regular evaluation, add standard metrics
            if metrics.pass_at_n:
                for k, value in metrics.pass_at_n.items():
                    summary[f"trajectory_pass_at_{k}"] = round(value, 4)
            if metrics.pass_hat_ks:
                for k, value in metrics.pass_hat_ks.items():
                    summary[f"trajectory_pass_hat_{k}"] = round(value, 4)
        elif config.evaluation_type == "trajectory_full_traj_rubric":
            # Full trajectory with rubric evaluation
            if metrics.pass_at_n:
                for k, value in metrics.pass_at_n.items():
                    summary[f"trajectory_full_traj_rubric_pass_at_{k}"] = round(value, 4)
            if metrics.pass_hat_ks:
                for k, value in metrics.pass_hat_ks.items():
                    summary[f"trajectory_full_traj_rubric_pass_hat_{k}"] = round(value, 4)
        elif config.evaluation_type == "trajectory_sliding_wo_rubric":
            # Sliding window without rubric evaluation
            if metrics.pass_at_n:
                for k, value in metrics.pass_at_n.items():
                    summary[f"trajectory_sliding_wo_rubric_pass_at_{k}"] = round(value, 4)
            if metrics.pass_hat_ks:
                for k, value in metrics.pass_hat_ks.items():
                    summary[f"trajectory_sliding_wo_rubric_pass_hat_{k}"] = round(value, 4)
        elif config.evaluation_type == "trajectory_full_traj_wo_rubric":
            # Full trajectory without rubric evaluation
            if metrics.pass_at_n:
                for k, value in metrics.pass_at_n.items():
                    summary[f"trajectory_full_traj_wo_rubric_pass_at_{k}"] = round(value, 4)
            if metrics.pass_hat_ks:
                for k, value in metrics.pass_hat_ks.items():
                    summary[f"trajectory_full_traj_wo_rubric_pass_hat_{k}"] = round(value, 4)

        return summary
    except Exception as e:
        print(f"Warning: Could not compute pass_at_k metrics: {e}")