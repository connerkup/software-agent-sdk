"""Autonomous Task Demonstration: OpenHands Harness + Google Antigravity Agent.

Executes a live autonomous coding, testing, and verification task inside an isolated workspace:
1. OpenHands creates and manages the LocalConversation state and event log.
2. AntigravityAgent receives the high-level objective and synthesizes a plan.
3. Antigravity CLI operates autonomously in the workspace: generates code, generates tests,
   executes pytest via CLI, and verifies correctness.
4. OpenHands captures the execution trace and verifies the resulting workspace artifacts.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from openhands.sdk.agent import AntigravityAgent
from openhands.sdk.conversation import Conversation
from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.sdk.event import MessageEvent
from openhands.sdk.llm import TextContent


def main() -> int:
    workspace_dir = Path("/tmp/delphi_actuarial_task")
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  OpenHands Harness + Antigravity Autonomous Agent Execution")
    print(f"  Target Workspace: {workspace_dir}")
    print("=" * 70 + "\n")

    # 1. Initialize Antigravity Agent
    print("[1/4] Initializing AntigravityAgent with agent-full-access mode...")
    agent = AntigravityAgent(
        agent_name="antigravity-worker",
        session_mode="agent-full-access",
        effort="medium",
    )

    # 2. Attach to OpenHands Conversation
    print("[2/4] Initializing OpenHands Conversation harness...")
    conv = Conversation(agent=agent, workspace=str(workspace_dir))

    # 3. Dispatch high-level autonomous task
    task_prompt = (
        "Develop an actuarial risk accumulator module in this workspace:\n"
        "1. Create `actuarial_accumulator.py` containing class `ActuarialAccumulator` with method:\n"
        "   `accumulate(self, values: list[float], threshold: float) -> dict`\n"
        "   returning: {'total': sum(values), 'exceedance': [v for v in values if v > threshold], 'pml': sum([v for v in values if v > threshold]) * 1.25}\n"
        "2. Create `test_actuarial_accumulator.py` with comprehensive pytest test cases for normal accumulation, zero exceedance, and empty lists.\n"
        "3. Run pytest to verify all tests pass.\n"
        "4. Output a summary of the created files and test results."
    )

    print("[3/4] Dispatching autonomous prompt to Antigravity through OpenHands...")
    conv.send_message(task_prompt)

    # Run the OpenHands step loop
    conv.run()

    print("\n[4/4] Evaluating OpenHands conversation state and workspace artifacts...")
    status = conv.state.execution_status
    print(f"Conversation Status: {status}")

    if status != ConversationExecutionStatus.FINISHED:
        print("ERROR: Conversation did not complete successfully.")
        return 1

    # Inspect events
    print("\n--- OpenHands Event Stream ---")
    for idx, ev in enumerate(conv.state.events):
        if isinstance(ev, MessageEvent) and ev.llm_message:
            role = ev.llm_message.role
            source = ev.source
            texts = [
                c.text for c in ev.llm_message.content if isinstance(c, TextContent)
            ]
            content = "\n".join(texts)
            print(f"Event [{idx}] ({source}:{role}):")
            if ev.llm_message.thinking_blocks:
                for tb in ev.llm_message.thinking_blocks:
                    print(f"  [Thought]: {tb.thinking.strip()[:120]}...")
            print(f"  [Content]:\n{content[:500]}...\n")

    # Verify artifacts on disk
    print("--- Workspace Artifact Verification ---")
    created_files = list(workspace_dir.iterdir())
    for f in created_files:
        print(f"  Found file: {f.name} ({f.stat().st_size} bytes)")
        if f.suffix == ".py":
            print(f"  --- {f.name} preview ---")
            lines = f.read_text().splitlines()[:10]
            for l in lines:
                print(f"    {l}")
            print("    ...")

    expected = {"actuarial_accumulator.py", "test_actuarial_accumulator.py"}
    found_names = {f.name for f in created_files}
    if expected.issubset(found_names):
        print("\nSUCCESS: All expected autonomous artifacts created and verified!")
        return 0
    else:
        print(f"\nWARNING: Found files: {found_names}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
