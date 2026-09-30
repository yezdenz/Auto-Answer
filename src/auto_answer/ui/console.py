"""
PowerShell / Terminal UI using Rich.
Provides colorized formatted output, panels, and spinners for smooth CLI experience.
"""

from __future__ import annotations
import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..ai.solver import AnswerResult

# Reconfigure stdout/stderr to utf-8 if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(safe_box=True)


def print_banner():
    """Prints the application banner in PowerShell/Terminal."""
    banner_text = Text()
    banner_text.append("╔═══════════════════════════════════════════════════╗\n", style="bold cyan")
    banner_text.append("║           🎯 AUTO ANSWER - AI ASSISTANT           ║\n", style="bold green")
    banner_text.append("║      Real-Time Screen Question & Exam Solver      ║\n", style="italic dim cyan")
    banner_text.append("╚═══════════════════════════════════════════════════╝", style="bold cyan")
    console.print(banner_text)


def display_answer_terminal(result: AnswerResult, elapsed_sec: Optional[float] = None):
    """
    Renders the extracted question, options, correct answer, and explanation in the terminal.
    """
    if not result.is_valid_question:
        console.print(
            Panel(
                "[bold yellow]⚠️ No clear question detected in the selected screen area.[/bold yellow]\n"
                "[dim]Try adjusting the scan region with the snipping tool or wait until the question is visible.[/dim]",
                title="[yellow]Scan Result[/yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    # Question Header
    q_content = Text()
    if result.is_negative_question:
        q_content.append("⚠️ NEGATIVE QUESTION (Select the FALSE / NOT choice)\n\n", style="bold red")

    q_content.append(result.question_text, style="bold white")

    time_badge = f" [dim]({elapsed_sec:.2f}s)[/dim]" if elapsed_sec is not None else ""
    console.print(
        Panel(
            q_content,
            title=f"[bold cyan]📝 {result.question_type.upper().replace('_', ' ')}{time_badge}[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )

    # Options Table
    if result.options:
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1), expand=True)
        table.add_column("Status", width=4, justify="center")
        table.add_column("Option", width=6)
        table.add_column("Text")

        for opt in result.options:
            is_correct = opt.is_correct or (opt.index in result.correct_option_indices)

            if is_correct:
                status_icon = "[bold green]✓[/bold green]"
                label_txt = f"[bold green][{opt.label}][/bold green]"
                content_txt = f"[bold green]{opt.text}[/bold green]"
            else:
                status_icon = "[dim]○[/dim]"
                label_txt = f"[dim][{opt.label}][/dim]"
                content_txt = f"[dim]{opt.text}[/dim]"

            table.add_row(status_icon, label_txt, content_txt)

        console.print(table)

    # Click Instruction Callout
    if result.click_instruction:
        console.print(
            Panel(
                f"[bold yellow]👉 {result.click_instruction}[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )

    # Correct Answer & Explanation Box
    pct = int(result.confidence * 100)
    conf_color = "green" if pct >= 80 else "yellow" if pct >= 60 else "red"

    ans_content = Text()
    ans_content.append("🎯 Best Answer: ", style="bold")
    ans_content.append(
        f"({result.correct_option_labels}) {result.correct_answer_text}\n\n",
        style="bold green",
    )
    ans_content.append("💡 Explanation: ", style="bold")
    ans_content.append(f"{result.explanation}\n", style="white")

    console.print(
        Panel(
            ans_content,
            title=f"[bold green]✅ SOLVED[/bold green] [dim]|[/dim] [{conf_color}]{pct}% confidence[/{conf_color}]",
            border_style="bright_green",
            box=box.HEAVY,
        )
    )
