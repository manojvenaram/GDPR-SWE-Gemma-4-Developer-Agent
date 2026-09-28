"""
src/harness/mock_swegemma.py
Local emulation harness for the Google Gemma 4 Developer Agent evaluation environment (swegemma).
Provides sandbox tool execution, code graph binding, and patch validation.
"""

from __future__ import annotations
import json
import os
import subprocess
from typing import Any, Callable, Dict, List, Optional
from src.graph.code_graph import CodeGraph, ASTCodeIndexer


class SwegemmaContext:
    """Emulates SwegemmaContext which hosts the repository environment and tool registry."""

    def __init__(self, workspace_path: str, code_graph: Optional[CodeGraph] = None):
        self.workspace_path = os.path.abspath(workspace_path)
        self.code_graph = code_graph or ASTCodeIndexer.index_repository(self.workspace_path)
        self.patch_submitted: bool = False
        self.submitted_diff: str = ""
        self.tool_registry: Dict[str, Callable[..., Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Registers the 9 standard competition tools."""
        self.tool_registry["run_command"] = self.run_command
        self.tool_registry["read_file"] = self.read_file
        self.tool_registry["edit_file"] = self.edit_file
        self.tool_registry["write_file"] = self.write_file
        self.tool_registry["get_status"] = self.get_status
        self.tool_registry["submit_patch"] = self.submit_patch
        self.tool_registry["get_code_neighbors"] = self.get_code_neighbors
        self.tool_registry["search_similar_code"] = self.search_similar_code
        self.tool_registry["get_code_subgraph"] = self.get_code_subgraph

    # Tool implementations
    def run_command(self, command: str) -> str:
        """Executes a command within the workspace sandbox."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = res.stdout + res.stderr
            return out if out else f"[Command exited with return code {res.returncode}]"
        except subprocess.TimeoutExpired:
            return "[Error: Command timed out after 60 seconds]"
        except Exception as e:
            return f"[Execution Error: {e}]"

    def read_file(
        self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
    ) -> str:
        """Reads a file or specified line range in the workspace."""
        full_path = os.path.join(self.workspace_path, file_path)
        if not os.path.exists(full_path):
            return f"[Error: File {file_path} not found]"

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s = max(1, start_line) if start_line is not None else 1
            e = min(total_lines, end_line) if end_line is not None else total_lines

            numbered_lines = [f"{i}: {lines[i-1]}" for i in range(s, e + 1)]
            return "".join(numbered_lines)
        except Exception as e:
            return f"[Error reading file: {e}]"

    def edit_file(self, file_path: str, target_content: str, replacement_content: str) -> str:
        """Performs exact substring replacement in a file."""
        full_path = os.path.join(self.workspace_path, file_path)
        if not os.path.exists(full_path):
            return f"[Error: File {file_path} not found]"

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if target_content not in content:
                return f"[Error: target_content not found in {file_path}. Ensure exact indentation and content match.]"

            occurrences = content.count(target_content)
            if occurrences > 1:
                return f"[Error: target_content occurs {occurrences} times. Must be uniquely identified.]"

            new_content = content.replace(target_content, replacement_content, 1)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"[Success: Successfully edited {file_path}]"
        except Exception as e:
            return f"[Error editing file: {e}]"

    def write_file(self, file_path: str, content: str) -> str:
        """Writes or creates a new file in the workspace."""
        full_path = os.path.join(self.workspace_path, file_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[Success: Wrote {len(content)} bytes to {file_path}]"
        except Exception as e:
            return f"[Error writing file: {e}]"

    def get_status(self) -> str:
        """Returns git diff and file status."""
        try:
            res = subprocess.run(
                "git status -s; git diff",
                shell=True,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            out = res.stdout
            return out if out.strip() else "[Working directory clean, no uncommitted changes]"
        except Exception as e:
            return f"[Status Error: {e}]"

    def submit_patch(self) -> str:
        """Submits the current git patch to the evaluation harness."""
        try:
            res = subprocess.run(
                "git diff",
                shell=True,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.submitted_diff = res.stdout
            self.patch_submitted = True
            return f"[Success: Patch submitted ({len(self.submitted_diff)} bytes)]"
        except Exception as e:
            return f"[Error generating patch: {e}]"

    # Graph intelligence tools
    def get_code_neighbors(
        self, node: str, edge_type: Optional[str] = None, max_neighbors: int = 50
    ) -> str:
        """Queries the code graph for incoming and outgoing neighbors."""
        neighbors = self.code_graph.get_neighbors(node, edge_type=edge_type, max_neighbors=max_neighbors)
        return json.dumps(neighbors, indent=2)

    def search_similar_code(self, query: str, max_results: int = 10) -> str:
        """Searches symbols and code entities using semantic keywords."""
        results = self.code_graph.search_similar(query, max_results=max_results)
        return json.dumps(results, indent=2)

    def get_code_subgraph(self, nodes: List[str], depth: int = 1) -> str:
        """Extracts the multi-hop topological subgraph around nodes."""
        subgraph = self.code_graph.get_subgraph(nodes, depth=depth)
        return json.dumps(subgraph, indent=2)
