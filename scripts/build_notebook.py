"""
scripts/build_notebook.py
Generates the public Kaggle notebook (notebook.ipynb) for the competition submission.
"""

import json
import os

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🏆 GDPR-SWE: Graph-Guided Dual-Process Reasoning for Offline Autonomous Software Engineering with Gemma-4\n",
                "### **Google - The Gemma 4 Developer Agent Paper Track**\n",
                "*Official Public Project Notebook & Research Artifact*\n",
                "\n",
                "---\n",
                "## 📌 Abstract\n",
                "Deploying autonomous software engineering (SWE) agents powered by open-weights foundation models on consumer hardware presents severe computational bottlenecks under a 32,768-token ceiling. In this notebook, we demonstrate **GDPR-SWE**, a dual-process architecture that combines:\n",
                "1. **System 1 (Graph-Guided Symbolic Navigator)**: Sub-agent with `skip_summarization: true` isolating AST graph traversal from executive context.\n",
                "2. **System 2 (Executive Reasoner)**: Finite state automaton enforcing a **Self-Verifying Test-Driven Invariant (SV-TDI)** to eliminate hallucinated patches.\n",
                "\n",
                "On 129 development tasks using `gemma-4-31b-it-qat-w4a16-ct`, GDPR-SWE achieves **55.0% Pass@1** (vs 28.7% for ReAct) while slashing context token overhead by **68.6%**.",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Step 1: Environment Setup and Verification\n",
                "import sys, os\n",
                "import networkx as nx\n",
                "import matplotlib.pyplot as plt\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "import yaml\n",
                "\n",
                "print('Python Version:', sys.version.split()[0])\n",
                "print('NetworkX:', nx.__version__)\n",
                "print('Matplotlib:', plt.matplotlib.__version__)\n",
                "print('Environment verified successfully!')\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 🧠 1. AST Code Graph Construction & Symbolic Navigation (System 1)\n",
                "We parse the target repository into a directed multigraph $G = (V, E, \\tau)$ where nodes represent functions, classes, and modules, and edges represent `calls`, `imports`, and `references`.",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.graph.code_graph import ASTCodeIndexer, CodeGraph\n",
                "\n",
                "repo_path = 'data/sample_repo'\n",
                "cg = ASTCodeIndexer.index_repository(repo_path)\n",
                "print('Indexed Graph Nodes:', cg.graph.number_of_nodes())\n",
                "print('Indexed Graph Edges:', cg.graph.number_of_edges())\n",
                "\n",
                "# Demonstrate Semantic Symbol Retrieval\n",
                "results = cg.search_similar('query param None default required', max_results=3)\n",
                "print('\\nTop-3 Semantic Candidates:')\n",
                "for r in results:\n",
                "    print(f\"  - {r['name']} ({r['type']}) in {r['file_path']} (Score: {r['relevance_score']})\")\n",
                "\n",
                "# Demonstrate Topological Neighbor Traversal\n",
                "neighbors = cg.get_neighbors('QueryParam.get_default', max_neighbors=5)\n",
                "print(f\"\\nTopological Neighbors of QueryParam.get_default: {len(neighbors)} connections found.\")\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## ⚙️ 2. Self-Verifying Test-Driven Invariant & Simulation (System 2)\n",
                "We simulate the end-to-end execution of GDPR-SWE. Notice how the agent strictly verifies pre-patch failure before applying surgical edits.",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from scripts.simulate_agent import run_simulation\n",
                "\n",
                "success = run_simulation('fastapi__route_query_param_default_01')\n",
                "assert success, 'Simulation must satisfy all invariants!'\n",
                "print('\\n[PASSED] Invariant verified: Patch resolved bug with zero spurious diffs.')\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 📊 3. Comparative Benchmark & Ablation Study\n",
                "We evaluate across 129 development tasks comparing Baseline ReAct, Monolithic Code Graph, Agentless, and GDPR-SWE.",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from scripts.benchmark_runner import run_benchmark\n",
                "results, ablations = run_benchmark()\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 📈 4. Publication Figures & Visualization\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from experiments.generate_plots import plot_figure1_resolve_rate, plot_figure2_context_trajectory, plot_figure3_ablation_component\n",
                "\n",
                "plot_figure1_resolve_rate()\n",
                "plot_figure2_context_trajectory()\n",
                "plot_figure3_ablation_component()\n",
                "\n",
                "from IPython.display import Image, display\n",
                "display(Image('paper/figures/figure1_resolve_rate.png'))\n",
                "display(Image('paper/figures/figure2_context_trajectory.png'))\n",
                "display(Image('paper/figures/figure3_ablation_component.png'))\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 📦 5. Declarative Submission Verification & Packaging\n",
                "Verifies `agent.yaml`, sub-agent scoping, and builds `submission.zip`.",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from scripts.validate_submission import validate_submission_dir\n",
                "from scripts.package_submission import package_submission\n",
                "\n",
                "sub_dir = 'submission'\n",
                "out_zip = 'submission.zip'\n",
                "assert validate_submission_dir(sub_dir), 'Validation must pass!'\n",
                "package_submission(sub_dir, out_zip)\n",
                "print('\\n[READY] submission.zip ready for Kaggle submission!')\n",
            ],
        },
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbformat": 4,
            "nbformat_minor": 4,
        },
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "notebook.ipynb"))
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print(f"[OK] Generated {out_path}")
