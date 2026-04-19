from __future__ import annotations

import argparse
import sys
from pathlib import Path

from orchestrator.controller import Orchestrator, RunConfig


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Agent orchestrator")
    p.add_argument("--plan", default=None, help="Plan id (agents/plans/<id>.json); required unless --resume")
    p.add_argument("--goal", default="Orchestrator smoke goal", help="Task text / template")
    p.add_argument(
        "--mode",
        choices=("simulate", "handoff", "execute"),
        default="simulate",
        help="simulate | handoff | execute (Anthropic API; needs ANTHROPIC_API_KEY)",
    )
    p.add_argument("--reuse-outputs", action="store_true", help="Skip steps when valid output JSON exists")
    p.add_argument("--run-id", default=None, help="Fixed run id (default: uuid)")
    p.add_argument(
        "--runs-dir",
        default=None,
        metavar="DIR",
        help="Per-project runs directory (default: ~/.claude/runs/ephemeral/)",
    )
    p.add_argument(
        "--resume",
        metavar="RUN_ID",
        default=None,
        help="Resume a handoff run: use with --advance or --finish",
    )
    p.add_argument(
        "--advance",
        action="store_true",
        help="After prior wave validated, run next handoff wave",
    )
    p.add_argument(
        "--finish",
        action="store_true",
        help="Validate all agent outputs then run builtin merge",
    )
    args = p.parse_args(argv)

    runs_dir = Path(args.runs_dir).resolve() if args.runs_dir else None
    orch = Orchestrator(runs_dir=runs_dir)

    if args.resume:
        if args.advance and args.finish:
            print("Use only one of --advance or --finish", file=sys.stderr)
            return 2
        if args.advance:
            path = orch.resume_handoff_advance(args.resume)
            print(path)
            return 0
        if args.finish:
            path = orch.resume_handoff_finish(args.resume)
            print(path)
            return 0
        print("With --resume, pass --advance or --finish", file=sys.stderr)
        return 2

    if not args.plan:
        print("--plan is required unless using --resume", file=sys.stderr)
        return 2

    cfg = RunConfig(
        plan_id=args.plan,
        goal=args.goal,
        mode=args.mode,
        reuse_outputs=args.reuse_outputs,
        run_id=args.run_id,
    )
    run_dir = orch.execute(cfg)
    print(run_dir)
    if args.mode == "handoff":
        runs_flag = f" --runs-dir {args.runs_dir}" if args.runs_dir else ""
        print(
            "Next: complete JSON in this directory, then:\n"
            f"  python3 -m orchestrator{runs_flag} --resume {run_dir.name} --advance\n"
            "Repeat until merged.json exists, or when all outputs are ready:\n"
            f"  python3 -m orchestrator{runs_flag} --resume {run_dir.name} --finish",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
