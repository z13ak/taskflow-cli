"""TaskFlow - a Rich-powered terminal task tracker."""

from __future__ import annotations

import argparse
import datetime
import sys

from rich.console import Console
from rich.table import Table

from taskflow import db

console = Console()

PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def validate_date(value: str) -> str:
    try:
        datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid date (use YYYY-MM-DD)") from exc
    return value


def cmd_add(args: argparse.Namespace) -> None:
    conn = db.get_connection()
    task_id = db.add_task(conn, args.text, args.priority, args.due)
    console.print(f"[green]Added[/] task [bold]#{task_id}[/]: {args.text}")


def cmd_list(args: argparse.Namespace) -> None:
    conn = db.get_connection()
    rows = db.list_tasks(conn, status=args.status)

    if not rows:
        console.print(f"[dim]No {args.status} tasks.[/]")
        return

    table = Table(title=f"TaskFlow - {args.status} tasks", show_lines=False)
    table.add_column("ID", justify="right", style="bold")
    table.add_column("Done", width=4)
    table.add_column("Task")
    table.add_column("Priority")
    table.add_column("Due")

    today = datetime.date.today().isoformat()
    for row in rows:
        check = "[green]x[/]" if row["done"] else " "
        priority_color = PRIORITY_COLORS.get(row["priority"], "white")
        priority_text = f"[{priority_color}]{row['priority']}[/]"

        due = row["due_date"] or "-"
        if row["due_date"] and not row["done"] and row["due_date"] < today:
            due = f"[red]{due} (overdue)[/]"

        text = row["text"]
        if row["done"]:
            text = f"[dim strike]{text}[/]"

        table.add_row(str(row["id"]), check, text, priority_text, due)

    console.print(table)


def cmd_done(args: argparse.Namespace) -> None:
    conn = db.get_connection()
    task = db.get_task(conn, args.id)
    if task is None:
        console.print(f"[red]No task with ID {args.id}.[/]")
        sys.exit(1)
    if task["done"]:
        console.print(f"[yellow]Task #{args.id} is already done.[/]")
        return
    db.mark_done(conn, args.id)
    console.print(f"[green]Completed[/] task [bold]#{args.id}[/]: {task['text']}")


def cmd_rm(args: argparse.Namespace) -> None:
    conn = db.get_connection()
    task = db.get_task(conn, args.id)
    if task is None:
        console.print(f"[red]No task with ID {args.id}.[/]")
        sys.exit(1)
    db.delete_task(conn, args.id)
    console.print(f"[green]Removed[/] task [bold]#{args.id}[/]: {task['text']}")


def cmd_stats(args: argparse.Namespace) -> None:
    conn = db.get_connection()
    stats = db.get_stats(conn)

    table = Table(title="TaskFlow - stats", show_header=False)
    table.add_column("metric", style="bold")
    table.add_column("value")

    completion = (stats["done"] / stats["total"] * 100) if stats["total"] else 0
    table.add_row("Total tasks", str(stats["total"]))
    table.add_row("Completed", f"{stats['done']} ({completion:.0f}%)")
    table.add_row("Pending", str(stats["pending"]))
    overdue_style = "red" if stats["overdue"] else "green"
    table.add_row("Overdue", f"[{overdue_style}]{stats['overdue']}[/]")

    for priority in ("high", "medium", "low"):
        count = stats["by_priority"].get(priority, 0)
        color = PRIORITY_COLORS[priority]
        table.add_row(f"  {priority} priority (pending)", f"[{color}]{count}[/]")

    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskflow", description="A terminal task tracker.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_add = subparsers.add_parser("add", help="Add a new task")
    p_add.add_argument("text", help="Task description")
    p_add.add_argument("--priority", choices=["low", "medium", "high"], default="medium")
    p_add.add_argument("--due", type=validate_date, default=None, help="Due date, YYYY-MM-DD")
    p_add.set_defaults(func=cmd_add)

    p_list = subparsers.add_parser("list", help="List tasks")
    p_list.add_argument(
        "status", nargs="?", choices=["pending", "done", "all"], default="pending"
    )
    p_list.set_defaults(func=cmd_list)

    p_done = subparsers.add_parser("done", help="Mark a task as complete")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)

    p_rm = subparsers.add_parser("rm", help="Delete a task")
    p_rm.add_argument("id", type=int)
    p_rm.set_defaults(func=cmd_rm)

    p_stats = subparsers.add_parser("stats", help="Show task statistics")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
