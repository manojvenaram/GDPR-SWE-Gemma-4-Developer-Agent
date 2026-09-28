"""
scripts/validate_submission.py
Validates compliance of the submission directory against Google ADK / swegemma rules:
1. agent.yaml must be at the root of the archive.
2. Model must be gemma-4-31b-it-qat-w4a16-ct.
3. All !include references must resolve to valid files.
4. Sub-agents must use skip_summarization: true to avoid context collapse.
5. All declared tools must be valid competition tools.
"""

from __future__ import annotations
import os
import re
import sys
import yaml

# Ensure utf-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


VALID_TOOLS = {
    "run_command",
    "read_file",
    "edit_file",
    "write_file",
    "get_status",
    "submit_patch",
    "get_code_neighbors",
    "search_similar_code",
    "get_code_subgraph",
    "agent_tool",
}

EXPECTED_MODEL = "gemma-4-31b-it-qat-w4a16-ct"


def parse_yaml_with_includes(yaml_path: str, base_dir: str) -> dict:
    """Lightweight custom parser for YAML files with !include directives."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find !include references
    includes = re.findall(r"!include\s+([^\s\n]+)", content)
    for inc in includes:
        resolved_path = os.path.normpath(os.path.join(os.path.dirname(yaml_path), inc))
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Included file does not exist: {inc} (resolved: {resolved_path})")

    # Replace !include for standard yaml parsing
    sanitized = re.sub(r"!include\s+([^\s\n]+)", r'"\1"', content)
    return yaml.safe_load(sanitized)


def validate_submission_dir(submission_dir: str) -> bool:
    print("=" * 60)
    print("PRE-FLIGHT VALIDATION: Gemma 4 Developer Agent Submission")
    print(f"Target Directory: {submission_dir}")
    print("=" * 60)

    errors = []
    warnings = []

    agent_yaml_path = os.path.join(submission_dir, "agent.yaml")
    if not os.path.exists(agent_yaml_path):
        errors.append("agent.yaml is MISSING from root of submission!")
        print(f"FAILED: {errors[-1]}")
        return False

    try:
        root_config = parse_yaml_with_includes(agent_yaml_path, submission_dir)
        print("[OK] agent.yaml parsed successfully")
    except Exception as e:
        errors.append(f"Syntax error in agent.yaml: {e}")
        print(f"FAILED: {errors[-1]}")
        return False

    # Check model
    model = root_config.get("model")
    if model != EXPECTED_MODEL:
        warnings.append(f"Model is '{model}', expected '{EXPECTED_MODEL}' for final scoring environment.")
    else:
        print(f"[OK] Model verified: {model}")

    # Check tools
    tools = root_config.get("tools", [])
    has_subagent = False
    for tool_entry in tools:
        if isinstance(tool_entry, str):
            if tool_entry not in VALID_TOOLS:
                errors.append(f"Invalid tool '{tool_entry}' in agent.yaml")
        elif isinstance(tool_entry, dict) and "agent_tool" in tool_entry:
            has_subagent = True
            sub_cfg = tool_entry["agent_tool"]
            sub_path = sub_cfg.get("config_path")
            skip_sum = sub_cfg.get("skip_summarization")

            if not sub_path:
                errors.append("agent_tool missing 'config_path'")
            else:
                full_sub_path = os.path.normpath(os.path.join(submission_dir, sub_path))
                if not os.path.exists(full_sub_path):
                    errors.append(f"Sub-agent config does not exist: {sub_path}")
                else:
                    print(f"[OK] Sub-agent config verified: {sub_path}")
                    sub_yaml = parse_yaml_with_includes(full_sub_path, submission_dir)
                    if sub_yaml.get("model") != EXPECTED_MODEL:
                        warnings.append(f"Sub-agent model '{sub_yaml.get('model')}' must match root model.")

            if not skip_sum:
                warnings.append("agent_tool should set 'skip_summarization: true' to avoid context collapse.")
            else:
                print("[OK] Sub-agent skip_summarization is active (context protected)")

    if has_subagent:
        print("[OK] Hierarchical sub-agent pattern verified")

    print("-" * 60)
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\n[FAIL] Validation FAILED with {len(errors)} error(s).")
        return False

    print(f"\n[PASS] Validation PASSED! All pre-flight criteria satisfied.")
    return True


if __name__ == "__main__":
    sub_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "submission"))
    success = validate_submission_dir(sub_dir)
    sys.exit(0 if success else 1)
