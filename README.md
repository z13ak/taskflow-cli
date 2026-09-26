# taskflow-cli

A terminal task tracker with color-coded priorities, due dates, and
completion stats — built with `argparse` and rendered with `rich`.

## Setup

```bash
pip install -e .
taskflow add "Ship the portfolio redesign" --priority high --due 2026-09-01
taskflow list
taskflow done 1
taskflow stats
```

Or run it without installing:

```bash
pip install -r requirements.txt
python -m taskflow add "Write the README"
python -m taskflow list
```

## Commands

| Command                             | Description                                  |
| ------------------------------------ | --------------------------------------------- |
| `taskflow add "text" [--priority] [--due]` | Add a task. Priority: low/medium/high (default medium). |
| `taskflow list [pending\|done\|all]` | List tasks as a colored table (default: pending). |
| `taskflow done <id>`                | Mark a task complete.                         |
| `taskflow rm <id>`                  | Delete a task.                                |
| `taskflow stats`                    | Completion rate, pending-by-priority, overdue count. |

Tasks are stored in SQLite at `~/.taskflow/tasks.db` (override with the
`TASKFLOW_DB` environment variable - useful for tests or per-project task lists).
