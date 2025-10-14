import json
from typing import List, Optional, Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from vita.data_model.message import (
    AssistantMessage,
    Message,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from vita.data_model.simulation import RunConfig, SimulationRun
from vita.data_model.tasks import Action, Task
from vita.metrics.agent_metrics import AgentMetrics, is_successful


class ConsoleDisplay:
    console = Console()

    @classmethod
    def display_run_config(cls, config: RunConfig):
        """
        Display the run configuration in a formatted way using Rich library.

        Args:
            config: The run configuration to display
        """
        def json_serializable(obj: Any) -> Any:
            """Convert object to JSON serializable format"""
            if hasattr(obj, '__class__') and obj.__class__.__name__ == 'type':
                return obj.__name__
            elif hasattr(obj, '__dict__'):
                return {k: json_serializable(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, (list, tuple)):
                return [json_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: json_serializable(v) for k, v in obj.items()}
            else:
                return obj

        layout = Layout()

        layout.split(Layout(name="header"), Layout(name="body"))

        layout["body"].split_row(
            Layout(name="agent", ratio=1),
            Layout(name="user", ratio=1),
            Layout(name="settings", ratio=1),
        )

        header_content = Panel(
            f"[white]Domain:[/] {config.domain}\n"
            f"[white]Task Set:[/] {config.task_set_name if config.task_set_name else 'Default'}\n"
            f"[white]Task IDs:[/] {', '.join(map(str, config.task_ids)) if config.task_ids else 'All'}\n"
            f"[white]Number of trials:[/] {config.num_trials}\n"
            f"[white]Max steps:[/] {config.max_steps}\n"
            f"[white]Max errors:[/] {config.max_errors}",
            title="[bold blue]Simulation Configuration",
            border_style="blue",
        )

        agent_content = Panel(
            f"[white]Implementation:[/] {config.agent}\n"
            f"[white]Model:[/] {config.llm_agent}\n"
            "[white]LLM Arguments:[/]\n"
            f"{json.dumps(json_serializable(config.llm_args_agent), indent=2)}",
            title="[bold cyan]Agent Configuration",
            border_style="cyan",
        )

        user_content = Panel(
            f"[white]Implementation:[/] {config.user}\n"
            f"[white]Model:[/] {config.llm_user}\n"
            "[white]LLM Arguments:[/]\n"
            f"{json.dumps(json_serializable(config.llm_args_user), indent=2)}",
            title="[bold cyan]User Configuration",
            border_style="cyan",
        )

        settings_content = Panel(
            f"[white]Save To:[/] {config.save_to or 'Not specified'}\n"
            f"[white]Max Concurrency:[/] {config.max_concurrency}",
            title="[bold cyan]Additional Settings",
            border_style="cyan",
        )

        layout["header"].update(header_content)
        layout["agent"].update(agent_content)
        layout["user"].update(user_content)
        layout["body"]["settings"].update(settings_content)

        cls.console.print(layout)

    @classmethod
    def display_task(cls, task: Task):
        content_parts = []

        if task.id is not None:
            content_parts.append(f"[white]ID:[/] {task.id}")

        scenario_parts = []
        if task.user_scenario.user_profile:
            scenario_parts.append(f"[white]Persona:[/] {task.user_scenario.user_profile}")

        scenario_parts.append(
            f"[white]Task Instructions:[/] {task.instructions}"
        )

        if scenario_parts:
            content_parts.append(
                "[bold cyan]User Scenario:[/]\n" + "\n".join(scenario_parts)
            )

        if task.evaluation_criteria:
            eval_parts = []
            if task.evaluation_criteria.expected_states:
                eval_parts.append(
                    f"[white]Expected States:[/]\n{json.dumps([s.model_dump() for s in task.evaluation_criteria.expected_states], indent=2, ensure_ascii=False)}"
                )
            if task.evaluation_criteria.overall_rubrics:
                eval_parts.append(
                    f"[white]Overall Rubrics:[/]\n{json.dumps(task.evaluation_criteria.overall_rubrics, indent=2, ensure_ascii=False)}"
                )
            if eval_parts:
                content_parts.append(
                    "[bold cyan]Evaluation Criteria:[/]\n" + "\n".join(eval_parts)
                )
        content = "\n\n".join(content_parts)

        task_panel = Panel(
            content, title="[bold blue]Task Details", border_style="blue", expand=True
        )

        cls.console.print(task_panel)

    @classmethod
    def display_simulation(cls, simulation: SimulationRun, show_details: bool = True):
        """
        Display the simulation content in a formatted way using Rich library.

        Args:
            simulation: The simulation object to display
            show_details: Whether to show detailed information
        """
        sim_info = Text()
        if show_details:
            sim_info.append("Simulation ID: ", style="bold cyan")
            sim_info.append(f"{simulation.id}\n")
        sim_info.append("Task ID: ", style="bold cyan")
        sim_info.append(f"{simulation.task_id}\n")
        sim_info.append("Trial: ", style="bold cyan")
        sim_info.append(f"{simulation.trial}\n")
        if show_details:
            sim_info.append("Start Time: ", style="bold cyan")
            sim_info.append(f"{simulation.start_time}\n")
            sim_info.append("End Time: ", style="bold cyan")
            sim_info.append(f"{simulation.end_time}\n")
        sim_info.append("Duration: ", style="bold cyan")
        sim_info.append(f"{simulation.duration:.2f}s\n")
        sim_info.append("Termination Reason: ", style="bold cyan")
        sim_info.append(f"{simulation.termination_reason}\n")
        if simulation.agent_cost is not None:
            sim_info.append("Agent Cost: ", style="bold cyan")
            sim_info.append(f"${simulation.agent_cost:.4f}\n")
        if simulation.user_cost is not None:
            sim_info.append("User Cost: ", style="bold cyan")
            sim_info.append(f"${simulation.user_cost:.4f}\n")
        if simulation.reward_info:
            marker = "✅" if is_successful(simulation.reward_info.reward) else "❌"
            sim_info.append("Reward: ", style="bold cyan")
            sim_info.append(f"{marker} {simulation.reward_info.reward:.4f}\n")
            
            # Display detailed reward breakdown
            if simulation.reward_info.reward_breakdown:
                sim_info.append("Reward Breakdown:\n", style="bold magenta")
                for reward_type, value in simulation.reward_info.reward_breakdown.items():
                    sim_info.append(f"  {reward_type.value}: {value:.4f}\n")

            if simulation.reward_info.nl_rubrics:
                sim_info.append("\nNL Assertions:\n", style="bold magenta")
                for i, assertion in enumerate(simulation.reward_info.nl_rubrics):
                    sim_info.append(
                        f"- {i}: {assertion.nl_rubric} {'✅' if assertion.met else '❌'}\n\t{assertion.justification}\n"
                    )

            if simulation.reward_info.info:
                sim_info.append("\nAdditional Info:\n", style="bold magenta")
                for key, value in simulation.reward_info.info.items():
                    sim_info.append(f"{key}: {value}\n")

        cls.console.print(
            Panel(sim_info, title="Simulation Overview", border_style="blue")
        )

        if simulation.messages:
            table = Table(
                title="Messages",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("Role", style="cyan", no_wrap=True)
            table.add_column("Content", style="green")
            table.add_column("Details", style="yellow")
            table.add_column("Turn", style="yellow", no_wrap=True)

            current_turn = None
            for msg in simulation.messages:
                content = msg.content if msg.content is not None else ""
                details = ""

                if isinstance(msg, AssistantMessage):
                    role_style = "bold blue"
                    content_style = "blue"
                    tool_style = "bright_blue"
                elif isinstance(msg, UserMessage):
                    role_style = "bold green"
                    content_style = "green"
                    tool_style = "bright_green"
                elif isinstance(msg, ToolMessage):
                    if msg.requestor == "user":
                        role_style = "bold green"
                        content_style = "bright_green"
                    else:
                        role_style = "bold blue"
                        content_style = "bright_blue"
                else:
                    role_style = "bold magenta"
                    content_style = "magenta"

                if isinstance(msg, AssistantMessage) or isinstance(msg, UserMessage):
                    if msg.tool_calls:
                        tool_calls = []
                        for tool in msg.tool_calls:
                            tool_calls.append(
                                f"[{tool_style}]Tool: {tool.name}[/]\n[{tool_style}]Args: {json.dumps(tool.arguments, indent=2, ensure_ascii=False)}[/]"
                            )
                        details = "\n".join(tool_calls)
                elif isinstance(msg, ToolMessage):
                    details = f"[{content_style}]Tool ID: {msg.id}. Requestor: {msg.requestor}[/]"
                    if msg.error:
                        details += " [bold red](Error)[/]"

                if current_turn is not None and msg.turn_idx != current_turn:
                    table.add_row("", "", "", "")
                current_turn = msg.turn_idx

                table.add_row(
                    f"[{role_style}]{msg.role}[/]",
                    f"[{content_style}]{content}[/]",
                    details,
                    str(msg.turn_idx) if msg.turn_idx is not None else "",
                )
            if show_details:
                cls.console.print(table)

    @classmethod
    def display_agent_metrics(cls, metrics: AgentMetrics):
        content = Text()

        # Check if we have all_types evaluation results
        if metrics.all_types_metrics:
            content.append("🔄 All Evaluation Types Results\n", style="bold blue")
            content.append("=" * 50 + "\n\n", style="dim")
            
            for eval_type, eval_metrics in metrics.all_types_metrics.items():
                content.append(f"📊 {eval_type.upper()} EVALUATION\n", style="bold green")
                content.append("🏆 Average Reward: ", style="bold cyan")
                content.append(f"{eval_metrics['avg_reward']:.4f}\n", style="white")
                
                # Display reward breakdown for this evaluation type
                if eval_metrics.get("avg_reward_breakdown"):
                    content.append("📊 Reward Breakdown:\n", style="bold cyan")
                    for reward_type, avg_value in eval_metrics["avg_reward_breakdown"].items():
                        content.append(f"  {reward_type}: ", style="bold white")
                        content.append(f"{avg_value:.4f}\n", style="white")
                
                if "pass_hat_ks" in eval_metrics:
                    content.append("📈 Pass^k Metrics:", style="bold cyan")
                    for k, pass_hat_k in eval_metrics["pass_hat_ks"].items():
                        content.append(f"\n  k={k}: ", style="bold white")
                        content.append(f"{pass_hat_k:.3f}", style="white")
                    content.append("\n")
                
                # Display pass@n and average@n metrics for each evaluation type
                if "pass_at_n" in eval_metrics:
                    content.append("📈 Pass@N Metrics:", style="bold cyan")
                    for n, pass_at_n_value in eval_metrics["pass_at_n"].items():
                        content.append(f"\n  N={n}: ", style="bold white")
                        content.append(f"{pass_at_n_value:.3f}", style="white")
                    content.append("\n")
                
                if "average_at_n" in eval_metrics:
                    content.append("📈 Average@N Metrics:", style="bold cyan")
                    for n, average_at_n_value in eval_metrics["average_at_n"].items():
                        content.append(f"\n  N={n}: ", style="bold white")
                        content.append(f"{average_at_n_value:.3f}", style="white")
                    content.append("\n")
                
                content.append("\n")
            
            content.append("💰 Average Cost per Conversation: ", style="bold cyan")
            content.append(f"${metrics.avg_agent_cost:.4f}\n", style="white")
            
        else:
            # Original display for single evaluation type
            content.append("🏆 Average Reward: ", style="bold cyan")
            content.append(f"{metrics.avg_reward:.4f}\n", style="white")

            # Display reward breakdown averages in the correct position
            if metrics.avg_reward_breakdown:
                content.append("📊 Reward Breakdown:\n", style="bold cyan")
                for reward_type, avg_value in metrics.avg_reward_breakdown.items():
                    content.append(f"  {reward_type}: ", style="bold white")
                    content.append(f"{avg_value:.4f}\n", style="white")

            content.append("\n📈 Pass^k Metrics:", style="bold cyan")
            for k, pass_hat_k in metrics.pass_hat_ks.items():
                content.append(f"\nk={k}: ", style="bold white")
                content.append(f"{pass_hat_k:.3f}", style="white")
            
            # Display pass@n and average@n metrics after Pass^k Metrics
            if metrics.pass_at_n:
                content.append("\n\n📈 Pass@N Metrics:", style="bold cyan")
                for n, pass_at_n_value in metrics.pass_at_n.items():
                    content.append(f"\nN={n}: ", style="bold white")
                    content.append(f"{pass_at_n_value:.3f}", style="white")
            
            if metrics.average_at_n:
                content.append("\n\n📈 Average@N Metrics:", style="bold cyan")
                for n, average_at_n_value in metrics.average_at_n.items():
                    content.append(f"\nN={n}: ", style="bold white")
                    content.append(f"{average_at_n_value:.3f}", style="white")

            content.append("\n\n💰 Average Cost per Conversation: ", style="bold cyan")
            content.append(f"${metrics.avg_agent_cost:.4f}\n", style="white")

        # Display total duration
        if metrics.total_duration:
            content.append(f"\n⏱️ Total Duration: ", style="bold cyan")
            content.append(f"{metrics.total_duration/60:.2f}min\n", style="white")

        metrics_panel = Panel(
            content,
            title="[bold blue]Agent Metrics",
            border_style="blue",
            expand=True,
        )

        cls.console.print(metrics_panel)


class MarkdownDisplay:
    @classmethod
    def display_actions(cls, actions: List[Action]) -> str:
        """Display actions in markdown format."""
        return f"```json\n{json.dumps([action.model_dump() for action in actions], indent=2, ensure_ascii=False)}\n```"

    @classmethod
    def display_messages(cls, messages: list[Message]) -> str:
        """Display messages in markdown format."""
        return "\n\n".join(cls.display_message(msg) for msg in messages)

    @classmethod
    def display_simulation(cls, sim: SimulationRun) -> str:
        """Display simulation in markdown format."""
        output = []

        output.append(f"**Task ID**: {sim.task_id}")
        output.append(f"**Trial**: {sim.trial}")
        output.append(f"**Duration**: {sim.duration:.2f}s")
        output.append(f"**Termination**: {sim.termination_reason}")
        if sim.agent_cost is not None:
            output.append(f"**Agent Cost**: ${sim.agent_cost:.4f}")
        if sim.user_cost is not None:
            output.append(f"**User Cost**: ${sim.user_cost:.4f}")

        if sim.reward_info:
            output.append(f"**Reward**: {sim.reward_info.reward:.4f}")
            
            # Display detailed reward breakdown
            if sim.reward_info.reward_breakdown:
                output.append("**Reward Breakdown**:")
                for reward_type, value in sim.reward_info.reward_breakdown.items():
                    output.append(f"- {reward_type.value}: {value:.4f}")

            if sim.reward_info.nl_rubrics:
                output.append("\n**NL Assertions**")
                for i, assertion in enumerate(sim.reward_info.nl_rubrics):
                    output.append(
                        f"- {i}: {assertion.nl_rubric} {'✅' if assertion.met else '❌'} {assertion.justification}"
                    )

            if sim.reward_info.info:
                output.append("\n**Additional Info**")
                for key, value in sim.reward_info.info.items():
                    output.append(f"- {key}: {value}")

        if sim.messages:
            output.append("\n**Messages**:")
            output.extend(cls.display_message(msg) for msg in sim.messages)

        return "\n\n".join(output)

    @classmethod
    def display_result(
        cls,
        task: Task,
        sim: SimulationRun,
        reward: Optional[float] = None,
        show_task_id: bool = False,
    ) -> str:
        """Display a single result with all its components in markdown format."""
        output = [
            f"## Task {task.id}" if show_task_id else "## Task",
            "\n### User Instruction",
            task.user_scenario.instructions,
        ]

        if reward is not None:
            output.extend(["\n### Reward", f"**{reward:.3f}**"])

        output.extend(["\n### Simulation", cls.display_simulation(sim)])

        return "\n".join(output)

    @classmethod
    def display_message(cls, msg: Message) -> str:
        """Display a single message in markdown format."""
        parts = []

        turn_prefix = f"[TURN {msg.turn_idx}] " if msg.turn_idx is not None else ""

        if isinstance(msg, AssistantMessage) or isinstance(msg, UserMessage):
            parts.append(f"{turn_prefix}**{msg.role}**:")
            if msg.content:
                parts.append(msg.content)
            if msg.tool_calls:
                tool_calls = []
                for tool in msg.tool_calls:
                    tool_calls.append(
                        f"**Tool Call**: {tool.name}\n```json\n{json.dumps(tool.arguments, indent=2, ensure_ascii=False)}\n```"
                    )
                parts.extend(tool_calls)

        elif isinstance(msg, ToolMessage):
            status = " (Error)" if msg.error else ""
            parts.append(f"{turn_prefix}**tool{status}**:")
            parts.append(f"Reponse to: {msg.requestor}")
            if msg.content:
                parts.append(f"```\n{msg.content}\n```")

        elif isinstance(msg, SystemMessage):
            parts.append(f"{turn_prefix}**system**:")
            if msg.content:
                parts.append(msg.content)

        return "\n".join(parts)
