"""
src/cli.py
Command-line interface for the gdpr-swe toolkit.
"""

from __future__ import annotations
import argparse
import os
import sys

# Ensure workspace root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def main():
    parser = argparse.ArgumentParser(
        prog="gdpr-swe",
        description="GDPR-SWE: Graph-Guided Dual-Process Developer Agent Toolkit for Gemma 4",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available sub-commands")

    # validate
    subparsers.add_parser("validate", help="Validate submission directory against swegemma schema")

    # package
    subparsers.add_parser("package", help="Build compliant submission.zip for Kaggle")

    # simulate
    subparsers.add_parser("simulate", help="Run end-to-end task simulation with invariant checking")

    # benchmark
    subparsers.add_parser("benchmark", help="Run comparative benchmark across 4 agent paradigms")

    # plots
    subparsers.add_parser("plots", help="Generate publication-grade figures")

    args = parser.parse_args()

    if args.command == "validate":
        from scripts.validate_submission import validate_submission_dir
        sub_dir = os.path.join(BASE_DIR, "submission")
        success = validate_submission_dir(sub_dir)
        sys.exit(0 if success else 1)

    elif args.command == "package":
        from scripts.package_submission import package_submission
        src = os.path.join(BASE_DIR, "submission")
        dest = os.path.join(BASE_DIR, "submission.zip")
        package_submission(src, dest)

    elif args.command == "simulate":
        from scripts.simulate_agent import run_simulation
        success = run_simulation()
        sys.exit(0 if success else 1)

    elif args.command == "benchmark":
        from scripts.benchmark_runner import run_benchmark
        run_benchmark()

    elif args.command == "plots":
        from experiments.generate_plots import (
            plot_figure1_resolve_rate,
            plot_figure2_context_trajectory,
            plot_figure3_ablation_component,
        )
        plot_figure1_resolve_rate()
        plot_figure2_context_trajectory()
        plot_figure3_ablation_component()
        print("Publication figures generated in paper/figures/")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
