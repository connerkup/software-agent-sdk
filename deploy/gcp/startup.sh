#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# OpenHands + Antigravity Orchestration Node Bootstrap (GCP Compute Engine)
# ==============================================================================

LOG_FILE="/var/log/antigravity-bootstrap.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[$(date -u)] === Starting Antigravity Orchestration Node Bootstrap ==="

# 1. Update and install system dependencies
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
    curl \
    git \
    tmux \
    jq \
    ca-certificates \
    build-essential \
    python3 \
    python3-venv \
    python3-pip

# 2. Setup user environment for 'conner' or default user
TARGET_USER="conner"
if ! id -u "${TARGET_USER}" >/dev/null 2>&1; then
    TARGET_USER="${SUDO_USER:-ubuntu}"
    if ! id -u "${TARGET_USER}" >/dev/null 2>&1; then
        useradd -m -s /bin/bash conner
        TARGET_USER="conner"
    fi
fi
USER_HOME=$(eval echo "~${TARGET_USER}")
echo "[$(date -u)] Target user is: ${TARGET_USER} (${USER_HOME})"

# 3. Install Astral uv
if ! command -v uv >/dev/null 2>&1; then
    echo "[$(date -u)] Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
fi

# 4. Clone software-agent-sdk feature fork
WORKSPACE_DIR="${USER_HOME}/workspaces"
REPO_DIR="${WORKSPACE_DIR}/software-agent-sdk"
mkdir -p "${WORKSPACE_DIR}"

if [ ! -d "${REPO_DIR}" ]; then
    echo "[$(date -u)] Cloning feature fork repository..."
    git clone -b feat/agy-orchestration-harness https://github.com/connerkup/software-agent-sdk.git "${REPO_DIR}"
else
    echo "[$(date -u)] Fetching latest feat/agy-orchestration-harness..."
    cd "${REPO_DIR}"
    git fetch origin feat/agy-orchestration-harness
    git checkout feat/agy-orchestration-harness
    git pull origin feat/agy-orchestration-harness
fi

# 5. Build Python Virtualenv and synchronize dependencies
echo "[$(date -u)] Synchronizing dependencies with uv..."
cd "${REPO_DIR}"
chown -R "${TARGET_USER}:${TARGET_USER}" "${WORKSPACE_DIR}"
sudo -u "${TARGET_USER}" /usr/local/bin/uv sync

# 6. Verify environment by executing test suite
echo "[$(date -u)] Running test verification..."
sudo -u "${TARGET_USER}" /usr/local/bin/uv run pytest tests/sdk/agent/test_antigravity_agent.py tests/tools/workflow/test_workflow_tool.py

# 7. Execute diamond DAG verification workflow
echo "[$(date -u)] Executing Antigravity Diamond DAG workflow..."
sudo -u "${TARGET_USER}" env OPENHANDS_SUPPRESS_BANNER=1 /usr/local/bin/uv run python examples/antigravity_orchestrated_workflow.py

# 8. Create Antigravity ACP Systemd Service
cat << 'SERVICE' > /etc/systemd/system/antigravity-acp.service
[Unit]
Description=Antigravity OpenHands ACP Server Bridge
After=network.target

[Service]
Type=simple
User=conner
WorkingDirectory=/home/conner/workspaces/software-agent-sdk
ExecStart=/usr/local/bin/uv run python -m openhands.sdk.agent.acp.antigravity
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Adjust user in systemd unit if needed
sed -i "s/User=conner/User=${TARGET_USER}/g" /etc/systemd/system/antigravity-acp.service
sed -i "s|/home/conner|${USER_HOME}|g" /etc/systemd/system/antigravity-acp.service

systemctl daemon-reload
systemctl enable antigravity-acp.service || true

echo "[$(date -u)] === Antigravity Orchestration Node Bootstrap Complete ==="
