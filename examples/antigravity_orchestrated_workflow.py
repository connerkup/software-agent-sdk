"""Antigravity Orchestrated Multi-Agent DAG Workflow.

Demonstrates using OpenHands as a foundation harness for Google Antigravity agents:
- Defining a diamond DAG of tasks using AgentTaskNode
- Heterogeneous agent dispatch with AntigravityAgent
- Dynamic prompt interpolation of parent outputs into downstream tasks
- Coordinated multi-agent execution
"""

from __future__ import annotations

import asyncio
import tempfile

from openhands.sdk.agent import AntigravityAgent
from openhands.sdk.conversation import Conversation
from openhands.tools.task.manager import TaskManager
from openhands.tools.workflow import AgentTaskNode
from openhands.tools.workflow.impl import WorkflowContext


async def main() -> None:
    print("================================================================")
    print("  OpenHands Harness :: Antigravity Multi-Agent DAG Orchestrator ")
    print("================================================================\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Initialize primary Antigravity orchestrator agent
        orchestrator_agent = AntigravityAgent(
            agent_name="antigravity-orchestrator",
            model_name="gemini-2.5-pro",
            session_mode="agent-full-access",
        )
        conversation = Conversation(agent=orchestrator_agent, workspace=tmp_dir)

        # 2. Attach task manager and create workflow context
        task_manager = TaskManager()
        task_manager.attach_parent(conversation)
        wf = WorkflowContext(
            parent_conversation=conversation,
            max_concurrency=4,
            manager=task_manager,
        )

        # 3. Define the diamond DAG with heterogeneous nodes and result interpolation
        nodes = {
            "spec_design": AgentTaskNode(
                prompt=(
                    "Architect Delphi Actuarial Core spatial grid specification:\n"
                    "- 1km x 1km PML accumulation grid\n"
                    "- Parametric wildfire trigger threshold definitions\n"
                    "- Decision boundary invariants"
                ),
                agent="antigravity",
                description="Spatial specification design",
            ),
            "actuarial_calc": AgentTaskNode(
                prompt=(
                    "Perform actuarial loss calculation based on specification:\n"
                    "{spec_design}\n\n"
                    "Compute 100-year and 250-year PML values for $25M portfolio."
                ),
                agent="antigravity",
                depends_on=["spec_design"],
                description="Quantitative PML modeling",
            ),
            "risk_review": AgentTaskNode(
                prompt=(
                    "Review actuarial bounds and assumptions based on specification:\n"
                    "{spec_design}\n\n"
                    "Verify wildfire hazard rate curves and regulatory constraints."
                ),
                agent="antigravity",
                depends_on=["spec_design"],
                description="Risk and compliance review",
            ),
            "executive_synthesis": AgentTaskNode(
                prompt=(
                    "Synthesize complete underwriting decision report:\n\n"
                    "--- Quantitative Modeling ---\n"
                    "{actuarial_calc}\n\n"
                    "--- Risk & Compliance ---\n"
                    "{risk_review}\n\n"
                    "Formulate binding carrier underwriting recommendation."
                ),
                agent="antigravity",
                depends_on=["actuarial_calc", "risk_review"],
                description="Final executive synthesis",
            ),
        }

        print("Executing Diamond DAG:")
        print("  [spec_design]")
        print("     ├──> [actuarial_calc] ──┐")
        print("     └──> [risk_review]    ──┴──> [executive_synthesis]\n")

        results = await wf.run_dag(nodes)

        print("\nWorkflow Execution Succeeded! Results Summary:\n")
        for node_id, output in results.items():
            print(f"=== Stage: {node_id} ===")
            print(output.strip())
            print("-" * 60)

        print("\nAll 4 DAG task nodes executed with full provenance & isolation.")


if __name__ == "__main__":
    asyncio.run(main())
