"""
src/graph/code_graph.py
Code Graph Engine for AST Analysis, Dependency Extraction, and Semantic Code Intelligence.
Emulates the competition harness code graph and provides local indexing capabilities.
"""

from __future__ import annotations
import ast
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx


class CodeGraph:
    """Directed multigraph representing code symbols, call relationships, and dependencies."""

    def __init__(self, repo_path: str = ""):
        self.repo_path = repo_path
        self.graph = nx.MultiDiGraph()
        self.symbol_index: Dict[str, Dict[str, Any]] = {}
        self.corpus: List[Tuple[str, str]] = []  # (symbol_id, text_corpus)

    def add_symbol(
        self,
        symbol_id: str,
        name: str,
        symbol_type: str,
        file_path: str,
        start_line: int,
        end_line: int,
        docstring: str = "",
        signature: str = "",
    ):
        """Register a code symbol in the graph."""
        node_data = {
            "name": name,
            "type": symbol_type,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "docstring": docstring,
            "signature": signature,
        }
        self.graph.add_node(symbol_id, **node_data)
        self.symbol_index[symbol_id] = node_data

        # Index for lightweight keyword/semantic retrieval
        search_blob = f"{name} {symbol_type} {file_path} {signature} {docstring}".lower()
        self.corpus.append((symbol_id, search_blob))

    def add_relation(self, source_id: str, target_id: str, edge_type: str):
        """Add a directed relation between symbols (e.g., calls, imports, inherits)."""
        if self.graph.has_node(source_id) and self.graph.has_node(target_id):
            self.graph.add_edge(source_id, target_id, edge_type=edge_type)

    def get_neighbors(
        self, node: str, edge_type: Optional[str] = None, max_neighbors: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve incoming and outgoing neighbors of a symbol in the code graph.
        Matches the behavior of `get_code_neighbors` tool.
        """
        matched_node = self._resolve_node_name(node)
        if not matched_node or not self.graph.has_node(matched_node):
            return []

        neighbors: List[Dict[str, Any]] = []

        # Outgoing edges (callees, dependencies)
        for _, neighbor, data in self.graph.out_edges(matched_node, data=True):
            if edge_type is None or data.get("edge_type") == edge_type:
                node_info = dict(self.graph.nodes[neighbor])
                node_info["symbol_id"] = neighbor
                node_info["direction"] = "outgoing"
                node_info["edge_type"] = data.get("edge_type")
                neighbors.append(node_info)
                if len(neighbors) >= max_neighbors:
                    return neighbors

        # Incoming edges (callers, dependents)
        for predecessor, _, data in self.graph.in_edges(matched_node, data=True):
            if edge_type is None or data.get("edge_type") == edge_type:
                node_info = dict(self.graph.nodes[predecessor])
                node_info["symbol_id"] = predecessor
                node_info["direction"] = "incoming"
                node_info["edge_type"] = data.get("edge_type")
                neighbors.append(node_info)
                if len(neighbors) >= max_neighbors:
                    return neighbors

        return neighbors

    def get_subgraph(self, nodes: List[str], depth: int = 1) -> Dict[str, Any]:
        """
        Extract the subgraph surrounding a set of target nodes up to `depth` hops.
        Matches the behavior of `get_code_subgraph` tool.
        """
        resolved_nodes: Set[str] = set()
        for n in nodes:
            res = self._resolve_node_name(n)
            if res:
                resolved_nodes.add(res)

        if not resolved_nodes:
            return {"nodes": [], "edges": []}

        subgraph_nodes = set(resolved_nodes)
        for _ in range(depth):
            boundary = set()
            for current in subgraph_nodes:
                if self.graph.has_node(current):
                    boundary.update(self.graph.successors(current))
                    boundary.update(self.graph.predecessors(current))
            subgraph_nodes.update(boundary)

        sub_g = self.graph.subgraph(subgraph_nodes)
        node_list = []
        for n, data in sub_g.nodes(data=True):
            item = dict(data)
            item["symbol_id"] = n
            node_list.append(item)

        edge_list = []
        for u, v, data in sub_g.edges(data=True):
            edge_list.append({"source": u, "target": v, "edge_type": data.get("edge_type")})

        return {"nodes": node_list, "edges": edge_list}

    def search_similar(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Keyword & term-frequency similarity retrieval over symbols and docstrings.
        Matches the behavior of `search_similar_code` tool.
        """
        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        if not tokens:
            return []

        scores: List[Tuple[float, str]] = []
        for symbol_id, text in self.corpus:
            score = 0.0
            node_data = self.graph.nodes[symbol_id]
            name_lower = node_data.get("name", "").lower()

            for token in tokens:
                if token in name_lower:
                    score += 5.0  # High weight for exact symbol name match
                if token in node_data.get("file_path", "").lower():
                    score += 2.0  # Weight for matching file path
                if token in text:
                    score += 1.0  # Docstring / context match

            if score > 0:
                scores.append((score, symbol_id))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, symbol_id in scores[:max_results]:
            item = dict(self.graph.nodes[symbol_id])
            item["symbol_id"] = symbol_id
            item["relevance_score"] = round(score, 2)
            results.append(item)

        return results

    def _resolve_node_name(self, name: str) -> Optional[str]:
        """Resolve a full symbol_id or shorthand symbol name."""
        if name in self.graph:
            return name
        for symbol_id, data in self.graph.nodes(data=True):
            if data.get("name") == name or symbol_id.endswith(f".{name}"):
                return symbol_id
        return None


class ASTCodeIndexer:
    """Parses Python source files and populates a CodeGraph."""

    @staticmethod
    def index_repository(repo_path: str) -> CodeGraph:
        cg = CodeGraph(repo_path)
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path).replace("\\", "/")
                    ASTCodeIndexer._index_file(full_path, rel_path, cg)
        return cg

    @staticmethod
    def _index_file(full_path: str, rel_path: str, cg: CodeGraph):
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return

        module_name = rel_path.replace(".py", "").replace("/", ".")
        cg.add_symbol(
            symbol_id=f"module:{module_name}",
            name=module_name,
            symbol_type="module",
            file_path=rel_path,
            start_line=1,
            end_line=len(content.splitlines()),
            docstring=ast.get_docstring(tree) or "",
        )

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                sym_id = f"func:{module_name}.{node.name}"
                sig = f"def {node.name}({', '.join(a.arg for a in node.args.args)})"
                cg.add_symbol(
                    symbol_id=sym_id,
                    name=node.name,
                    symbol_type="function",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno + 10),
                    docstring=ast.get_docstring(node) or "",
                    signature=sig,
                )
                cg.add_relation(f"module:{module_name}", sym_id, "contains")

            elif isinstance(node, ast.ClassDef):
                class_id = f"class:{module_name}.{node.name}"
                cg.add_symbol(
                    symbol_id=class_id,
                    name=node.name,
                    symbol_type="class",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno + 20),
                    docstring=ast.get_docstring(node) or "",
                )
                cg.add_relation(f"module:{module_name}", class_id, "contains")

                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"method:{module_name}.{node.name}.{subnode.name}"
                        sig = f"def {subnode.name}({', '.join(a.arg for a in subnode.args.args)})"
                        cg.add_symbol(
                            symbol_id=method_id,
                            name=f"{node.name}.{subnode.name}",
                            symbol_type="method",
                            file_path=rel_path,
                            start_line=subnode.lineno,
                            end_line=getattr(subnode, "end_lineno", subnode.lineno + 10),
                            docstring=ast.get_docstring(subnode) or "",
                            signature=sig,
                        )
                        cg.add_relation(class_id, method_id, "contains")
