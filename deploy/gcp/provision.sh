#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Provision Antigravity Orchestration Node on Google Cloud Compute Engine
# ==============================================================================

INSTANCE_NAME="${1:-agy-orchestrator-1}"
ZONE="${2:-us-central1-a}"
MACHINE_TYPE="${3:-t2a-standard-4}" # Tau T2A ARM (4 vCPU / 16 GB RAM) or c3-standard-4
PROJECT="${GCP_PROJECT:-main-project-482516}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STARTUP_SCRIPT="${SCRIPT_DIR}/startup.sh"

echo "================================================================="
echo " Provisioning Antigravity Orchestration Node on GCP"
echo " Instance:     ${INSTANCE_NAME}"
echo " Zone:         ${ZONE}"
echo " Machine Type: ${MACHINE_TYPE}"
echo " Project:      ${PROJECT}"
echo " Startup:      ${STARTUP_SCRIPT}"
echo "================================================================="

if ! command -v gcloud >/dev/null 2>&1; then
    echo "ERROR: gcloud CLI not found in PATH." >&2
    exit 1
fi

gcloud compute instances create "${INSTANCE_NAME}" \
    --project="${PROJECT}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE_TYPE}" \
    --image-family="ubuntu-2404-lts-arm64" \
    --image-project="ubuntu-os-cloud" \
    --boot-disk-size="60GB" \
    --boot-disk-type="pd-balanced" \
    --scopes="cloud-platform" \
    --tags="antigravity,openhands-harness,mesh-node" \
    --metadata-from-file="startup-script=${STARTUP_SCRIPT}" \
    --metadata="enable-oslogin=TRUE"

echo ""
echo "Instance ${INSTANCE_NAME} created successfully."
echo "Follow provisioning logs with:"
echo "  gcloud compute instances get-serial-port-output ${INSTANCE_NAME} --zone=${ZONE} --port=1"
echo "Or SSH into the instance with:"
echo "  gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE}"
