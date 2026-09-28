"""
src/agent/state_machine.py
Finite State Automaton, Budget Gate, and Self-Verifying Invariant Enforcement for GDPR-SWE.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentPhase(str, Enum):
    LOCALIZATION = "LOCALIZATION"
    REPRODUCTION = "REPRODUCTION"
    MUTATION = "MUTATION"
    VERIFICATION = "VERIFICATION"
    SUBMISSION = "SUBMISSION"
    TERMINATED = "TERMINATED"


@dataclass
class BudgetGate:
    """Tracks token consumption, tool invocations, and halts before budget exhaustion."""
    max_steps: int = 25
    max_tokens: int = 32768
    current_step: int = 0
    estimated_tokens: int = 0
    tool_counts: Dict[str, int] = field(default_factory=dict)

    def record_action(self, tool_name: str, input_tokens: int = 0, output_tokens: int = 0) -> bool:
        """Records a tool execution and checks if budget allows continuation."""
        self.current_step += 1
        self.estimated_tokens += (input_tokens + output_tokens)
        self.tool_counts[tool_name] = self.tool_counts.get(tool_name, 0) + 1

        if self.current_step >= self.max_steps:
            return False
        if self.estimated_tokens >= self.max_tokens:
            return False
        return True

    @property
    def remaining_steps(self) -> int:
        return max(0, self.max_steps - self.current_step)

    @property
    def budget_exhausted(self) -> bool:
        return self.current_step >= self.max_steps or self.estimated_tokens >= self.max_tokens


@dataclass
class InvariantState:
    """Tracks the state invariants of the Self-Verifying Test-Driven Patching protocol."""
    fault_localized: bool = False
    fault_file: Optional[str] = None
    fault_symbol: Optional[str] = None
    reproduction_script_created: bool = False
    reproduction_pre_patch_failed: bool = False
    mutation_applied: bool = False
    reproduction_post_patch_passed: bool = False
    regression_tests_passed: bool = False
    reproduction_script_cleaned: bool = False
    patch_submitted: bool = False

    def is_invariant_satisfied(self) -> bool:
        """
        Self-Verifying Test-Driven Invariant (SV-TDI):
        A patch is valid only if:
        1. Pre-patch test failed
        2. Post-patch test passed
        3. Temporary test cleaned
        4. Patch applied
        """
        return (
            self.reproduction_pre_patch_failed
            and self.mutation_applied
            and self.reproduction_post_patch_passed
            and self.reproduction_script_cleaned
            and self.patch_submitted
        )


class GDPRStateMachine:
    """Enforces valid phase transitions in the dual-process reasoning cycle."""

    def __init__(self, budget_gate: Optional[BudgetGate] = None):
        self.current_phase = AgentPhase.LOCALIZATION
        self.budget = budget_gate or BudgetGate()
        self.invariants = InvariantState()
        self.transition_log: List[Dict[str, Any]] = []

    def transition_to(self, next_phase: AgentPhase, reason: str = "") -> bool:
        """Validates and executes a state transition."""
        allowed_transitions = {
            AgentPhase.LOCALIZATION: [AgentPhase.REPRODUCTION, AgentPhase.TERMINATED],
            AgentPhase.REPRODUCTION: [AgentPhase.MUTATION, AgentPhase.LOCALIZATION, AgentPhase.TERMINATED],
            AgentPhase.MUTATION: [AgentPhase.VERIFICATION, AgentPhase.TERMINATED],
            AgentPhase.VERIFICATION: [AgentPhase.MUTATION, AgentPhase.SUBMISSION, AgentPhase.TERMINATED],
            AgentPhase.SUBMISSION: [AgentPhase.TERMINATED],
            AgentPhase.TERMINATED: [],
        }

        if next_phase not in allowed_transitions[self.current_phase]:
            return False

        old_phase = self.current_phase
        self.current_phase = next_phase
        self.transition_log.append({
            "from": old_phase.value,
            "to": next_phase.value,
            "step": self.budget.current_step,
            "reason": reason,
        })
        return True

    def record_tool_execution(self, tool_name: str, args: Dict[str, Any], result: str):
        """Monitors tool calls and automatically updates invariant tracking."""
        self.budget.record_action(tool_name)

        if tool_name == "code_analyzer":
            self.invariants.fault_localized = True
            if "fault_file" in result:
                self.invariants.fault_file = args.get("fault_file")

        elif tool_name == "write_file" and "reproduce_issue.py" in args.get("file_path", ""):
            self.invariants.reproduction_script_created = True

        elif tool_name == "run_command" and any(k in args.get("command", "") for k in ["rm", "remove", "clean", "del", "unlink"]):
            if "reproduce_issue.py" in args.get("command", ""):
                self.invariants.reproduction_script_cleaned = True

        elif tool_name == "run_command" and "reproduce_issue.py" in args.get("command", ""):
            is_failure = "FAIL" in result or "AssertionError" in result or "Traceback" in result or "error" in result.lower()
            if not self.invariants.mutation_applied:
                if is_failure:
                    self.invariants.reproduction_pre_patch_failed = True
            else:
                if not is_failure and "error" not in result.lower():
                    self.invariants.reproduction_post_patch_passed = True

        elif tool_name == "edit_file":
            self.invariants.mutation_applied = True

        elif tool_name == "submit_patch":
            self.invariants.patch_submitted = True
            self.transition_to(AgentPhase.SUBMISSION, reason="submit_patch invoked")
            self.transition_to(AgentPhase.TERMINATED, reason="Task completed")
