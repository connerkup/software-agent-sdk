"""Tests for AntigravityAgent and AntigravityACPServer."""

from __future__ import annotations

import asyncio
import socket

import pytest
from acp.agent.connection import AgentSideConnection
from acp.client.connection import ClientSideConnection
from acp.schema import TextContentBlock

from openhands.sdk.agent import AntigravityAgent
from openhands.sdk.agent.acp.antigravity import AntigravityACPServer
from openhands.sdk.conversation import Conversation
from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.sdk.subagent.registry import get_agent_factory
from openhands.tools.task.manager import TaskManager


def test_antigravity_agent_attributes_and_registration():
    agent = AntigravityAgent()
    assert agent.agent_name == "antigravity"
    assert agent.model_name == "gemini-2.5-pro"
    assert agent.session_mode == "agent-full-access"
    assert agent.agent_kind == "openhands"

    # Verify registered in subagent factory
    factory = get_agent_factory("antigravity")
    assert factory is not None
    assert factory.definition.name == "antigravity"
    sub_agent = factory.factory_func(agent.llm)
    assert isinstance(sub_agent, AntigravityAgent)


def test_antigravity_agent_local_conversation_turn(tmp_path):
    agent = AntigravityAgent()
    conv = Conversation(agent=agent, workspace=str(tmp_path))
    conv.send_message("Synthesize spatial cat risk grid")
    conv.run()

    assert conv.state.execution_status == ConversationExecutionStatus.FINISHED
    events = conv.state.events
    assert len(events) >= 3
    # First is user message
    assert events[0].source == "user"
    # Second is agent thought
    assert events[1].source == "agent"
    assert events[1].llm_message.thinking_blocks is not None
    assert len(events[1].llm_message.thinking_blocks) > 0
    assert (
        "Synthesize spatial cat risk grid"
        in events[1].llm_message.thinking_blocks[0].thinking
    )
    # Third is agent final response
    assert events[2].source == "agent"
    assert "Antigravity Agent" in events[2].llm_message.content[0].text


def test_task_manager_dispatches_antigravity_subagent(tmp_path):
    agent = AntigravityAgent()
    parent_conv = Conversation(agent=agent, workspace=str(tmp_path))
    manager = TaskManager()
    manager.attach_parent(parent_conv)

    task = manager.start_task(
        prompt="Underwrite parametric fire risk threshold",
        subagent_type="antigravity",
        conversation=parent_conv,
    )
    assert task.status == "completed"
    assert task.result is not None
    assert "Antigravity Agent" in task.result


@pytest.mark.asyncio
async def test_antigravity_acp_server_protocol_lifecycle():
    class TestClient:
        def __init__(self):
            self.updates = []

        async def session_update(self, session_id, update, **kwargs):
            self.updates.append(update)

    s_agent, s_client = socket.socketpair()
    reader_a, writer_a = await asyncio.open_connection(sock=s_agent)
    reader_c, writer_c = await asyncio.open_connection(sock=s_client)

    server = AntigravityACPServer()
    client = TestClient()

    agent_conn = AgentSideConnection(
        server, writer_a, reader_a, listening=False, use_unstable_protocol=True
    )
    client_conn = ClientSideConnection(
        client, writer_c, reader_c, use_unstable_protocol=True
    )

    listen_task = asyncio.create_task(agent_conn.listen())

    try:
        # 1. Initialize
        init_res = await client_conn.initialize(1)
        assert init_res.agent_info is not None
        assert init_res.agent_info.name == "openhands-acp-antigravity"
        assert init_res.agent_capabilities.session_capabilities is not None
        assert init_res.agent_capabilities.session_capabilities.fork is not None
        assert init_res.agent_capabilities.session_capabilities.close is not None

        # 2. New session
        sess_res = await client_conn.new_session(cwd="/tmp")
        sess_id = sess_res.session_id
        assert sess_id is not None
        assert sess_res.models is not None
        assert sess_res.models.current_model_id == "gemini-2.5-pro"

        # 3. Model switch
        await client_conn.set_session_model("gemini-2.5-flash", session_id=sess_id)
        assert server._sessions[sess_id].model == "gemini-2.5-flash"

        # 4. Mode switch
        await client_conn.set_session_mode("plan", session_id=sess_id)
        assert server._sessions[sess_id].mode == "plan"

        # 5. Prompt turn
        prompt_res = await client_conn.prompt(
            [TextContentBlock(type="text", text="Evaluate PML scenario")],
            session_id=sess_id,
        )
        assert prompt_res.stop_reason == "end_turn"
        assert len(client.updates) >= 2

        # Check thought and text updates
        update_types = [type(u).__name__ for u in client.updates]
        assert "AgentThoughtChunk" in update_types
        assert "AgentMessageChunk" in update_types

        # 6. Close session
        await client_conn.close_session(session_id=sess_id)
        assert sess_id not in server._sessions

    finally:
        listen_task.cancel()
        await client_conn.close()
        await agent_conn.close()
