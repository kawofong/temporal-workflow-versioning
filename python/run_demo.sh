#!/usr/bin/env bash
# run_demo.sh — CardWorkflow Worker Versioning Demo
#
# This script walks through the demo step by step.
# Commands are displayed for you to copy and paste into separate terminals.

set -euo pipefail

# ─── Colors & formatting ──────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m'

# ─── UI helpers ───────────────────────────────────────────────────────────────
header() {
  echo
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${BLUE}  $1${NC}"
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo
}

note() {
  echo -e "  ${YELLOW}💡 $1${NC}"
}

section() {
  echo -e "\n  ${BOLD}${WHITE}$1${NC}"
}

diagram() {
  echo -e "  ${MAGENTA}$1${NC}"
}

# Display a command the user should run in another terminal.
cmd() {
  local label="${2:-}"
  [ -n "$label" ] && echo -e "\n  ${BOLD}▶  $label${NC}"
  local continued=false
  while IFS= read -r line; do
    if $continued; then
      printf "  ${CYAN}  %s${NC}\n" "$line"
    else
      printf "  ${CYAN}\$ %s${NC}\n" "$line"
    fi
    [[ "$line" == *\\ ]] && continued=true || continued=false
  done <<< "$1"
  echo
}

expect() {
  echo -e "  ${GREEN}✓  Expected: $1${NC}"
}

warn() {
  echo -e "  ${RED}⚠  $1${NC}"
}

pause() {
  echo
  echo -e "  ${DIM}────────────────────────────────────────────────────────────────${NC}"
  read -n 1 -s -r -p "  Press any key for the next step..."
  echo -e "\n"
}

# ─── Step 0: Prerequisites ────────────────────────────────────────────────────
step_prerequisites() {
  header "Step 1 — Prerequisites"

  note "Make sure you are inside the python/ directory for worker and starter commands."

  section "Scenario overview:"
  echo
  diagram "  CardWorkflow (PINNED + CaN upgrade)"
  diagram ""
  diagram "  Billing cycle: 150 s  │  CaN threshold: 50 events"
  diagram ""
  diagram "  ┌─ v1 run (PINNED to card-service:v1.0) ─────────────────────┐"
  diagram "  │  sleep(150 s)                                               │"
  diagram "  │  → generate_statement(account_id, cycle, transactions)      │"
  diagram "  │  → rewards += total_spend * 1   (inline, no activity)      │"
  diagram "  │  → send_statement_notification(statement, rewards)          │"
  diagram "  │  → [history ≥ 50 OR version changed?] ──Yes──► CaN ────────┼──►"
  diagram "  └─────────────────────────────────────────────────────────────┘"
  diagram ""
  diagram "  ┌─ v2 run (starts on card-service:v2.0 via CaN AUTO_UPGRADE) ┐"
  diagram "  │  sleep(150 s)                                               │"
  diagram "  │  → generate_statement(account_id, cycle, transactions)      │"
  diagram "  │  → persist_statement(statement)          ← NEW in v2       │"
  diagram "  │  → rewards += total_spend * 1   (inline, no activity)      │"
  diagram "  │  → send_statement_notification(statement, rewards)          │"
  diagram "  │  → [history ≥ 50 OR version changed?] ──Yes──► CaN ────────┼──►"
  diagram "  └─────────────────────────────────────────────────────────────┘"
  diagram ""
  diagram "  Key insight: adding persist_statement in v2 introduces a new"
  diagram "  command into the sequence — but NO PATCHING is needed because"
  diagram "  each run executes entirely on one version (PINNED)."

  pause
}

# ─── Step 1: Start Temporal dev server ───────────────────────────────────────
step_start_server() {
  header "Step 2 — Start the Temporal Development Server"

  if nc -z localhost 7233 2>/dev/null; then
    echo -e "  ${GREEN}✓  Temporal server already running on localhost:7233 — skipping.${NC}"
  else
    section "Open a new terminal and run:"
    cmd "temporal server start-dev" "Terminal 1 — Temporal Server"

    echo
    expect "Server listening on localhost:7233"
    expect "Web UI available at http://localhost:8233"
    echo
    note "Leave this terminal running for the entire demo."

    pause
  fi

  note "Open http://localhost:8233 in your browser to follow along visually."

  echo
  section "Architecture at this point:"
  echo
  diagram "  ┌────────────────────────────────────────────┐"
  diagram "  │           Temporal Server  :7233            │"
  diagram "  │   Event History │ Task Queues │ Visibility  │"
  diagram "  └────────────────────────────────────────────┘"
  diagram "                 (no workers yet)"

  pause
}

# ─── Step 2: Start Worker v1 ──────────────────────────────────────────────────
step_start_worker_v1() {
  header "Step 3 — Start Worker v1  (build_id = v1.0)"

  section "Open a second terminal and run:"
  cmd "cd python
BUILD_ID=v1.0 uv run worker.py" "Terminal 2 — Worker v1"

  echo
  expect "Worker started — deployment=card-service build_id=v1.0"
  expect "Worker is now polling card-task-queue"
  echo
  note "BUILD_ID identifies this exact version of the code."
  note "The worker registers with the Temporal server as 'card-service:v1.0'."

  echo
  section "Architecture at this point:"
  echo
  diagram "  ┌──────────────────────────────────────────────────┐"
  diagram "  │                Temporal Server                    │"
  diagram "  └──────────────────────────────────────────────────┘"
  diagram "                        ▲  poll card-task-queue"
  diagram "                        │"
  diagram "  ┌──────────────────────────────────────────────────┐"
  diagram "  │  Worker  card-service:v1.0                        │"
  diagram "  │  CardWorkflow (PINNED)  │  card activities        │"
  diagram "  └──────────────────────────────────────────────────┘"
  diagram "                  status: INACTIVE (not yet current)"

  pause
}

# ─── Step 3: Activate v1 ──────────────────────────────────────────────────────
step_activate_v1() {
  header "Step 4 — Activate v1 as the Current Deployment Version"

  section "Run in any terminal:"
  cmd "temporal worker deployment set-current-version \\
  --deployment-name card-service \\
  --build-id v1.0" "Activate v1"

  echo
  expect "card-service:v1.0 is now the Current version"
  echo
  note "Until a version is set as 'Current', new workflow executions are not routed to it."
  note "After this command, all new CardWorkflow starts will land on v1.0."
  note "You can verify with:"

  cmd "temporal worker deployment describe --name card-service" "Inspect deployment"

  echo
  section "Architecture at this point:"
  echo
  diagram "  ┌──────────────────────────────────────────────────┐"
  diagram "  │                Temporal Server                    │"
  diagram "  │  Deployment: card-service                         │"
  diagram "  │  └─ v1.0  ◄── CURRENT  ✓                         │"
  diagram "  └──────────────────────────────────────────────────┘"
  diagram "                        ▲"
  diagram "  ┌──────────────────────────────────────────────────┐"
  diagram "  │  Worker  card-service:v1.0  (polling)             │"
  diagram "  └──────────────────────────────────────────────────┘"

  pause
}

# ─── Step 4: Start CardWorkflow ───────────────────────────────────────────────
step_start_workflow() {
  header "Step 5 — Start the CardWorkflow and Send Transactions"

  section "Open a third terminal and run:"
  cmd "cd python
uv run -m workflows.card" "Terminal 3 — Starter"

  echo
  expect "Started CardWorkflow — workflow_id=card-ACC-001"
  expect "Signalled 4 transactions (Whole Foods, Netflix, Delta Airlines, Starbucks)"
  echo
  note "starter.py starts the workflow and immediately sends 4 transaction signals."
  note "The workflow is PINNED — it will remain on card-service:v1.0 for its entire run."

  echo
  section "You can send additional transactions at any time:"
  cmd "temporal workflow signal \\
  --workflow-id card-ACC-001 \\
  --name record_transaction \\
  --input '{\"amount\": 75.00, \"merchant\": \"Amazon\"}'" "Signal a transaction"

  echo
  section "Architecture at this point:"
  echo
  diagram "  CardWorkflow (card-ACC-001)"
  diagram "  ├─ version: card-service:v1.0   ← PINNED"
  diagram "  ├─ status:  Running"
  diagram "  ├─ cycle:   1"
  diagram "  └─ pending transactions: 4  (waiting for 30 s billing cycle)"

  pause
}

# ─── Step 5: Inspect the workflow ─────────────────────────────────────────────
step_inspect_workflow() {
  header "Step 6 — Inspect the Running Workflow"

  section "Describe the workflow to see its versioning info:"
  cmd "temporal workflow describe -w card-ACC-001" "Describe workflow"

  echo
  expect "Versioning Info:"
  expect "  Behavior:  Pinned"
  expect "  Version:   card-service:v1.0"
  echo
  note "PINNED means this execution will never move to a newer worker version."
  note "Even after we deploy v2, this run stays on v1 until it does CaN."

  section "Query accumulated rewards points:"
  cmd "temporal workflow query \\
  --workflow-id card-ACC-001 \\
  --type get_rewards_points" "Query workflow"

  echo
  section "List all active deployments:"
  cmd "temporal worker deployment describe --name card-service" "Describe deployment"

  echo
  note "Wait ~30 seconds to watch the first billing cycle complete in the worker logs."

  pause
}

# ─── Step 6: Update the code (v2 change) ─────────────────────────────────────
step_update_code() {
  header "Step 7 — Prepare Worker v2  (add persist_statement Activity)"

  section "In  python/workflows/card.py,  uncomment the persist_statement call:"
  echo
  echo -e "  ${DIM}Before (v1):${NC}"
  echo -e "  ${RED}      # await workflow.execute_activity(${NC}"
  echo -e "  ${RED}      #     persist_statement,${NC}"
  echo -e "  ${RED}      #     args=[statement],${NC}"
  echo -e "  ${RED}      #     start_to_close_timeout=timedelta(seconds=10),${NC}"
  echo -e "  ${RED}      # )${NC}"
  echo
  echo -e "  ${DIM}After (v2):${NC}"
  echo -e "  ${GREEN}      await workflow.execute_activity(${NC}"
  echo -e "  ${GREEN}          persist_statement,${NC}"
  echo -e "  ${GREEN}          args=[statement],${NC}"
  echo -e "  ${GREEN}          start_to_close_timeout=timedelta(seconds=10),${NC}"
  echo -e "  ${GREEN}      )${NC}"
  echo
  note "persist_statement adds a new Activity to the command sequence — normally"
  note "this would require patching for AUTO_UPGRADE workflows. Here it does NOT:"
  note "CardWorkflow is PINNED, so the in-flight v1 run completes entirely on v1"
  note "(without persist_statement). The v2 run starts fresh after CaN with the"
  note "full new sequence already baked in. No patch markers needed."

  pause
}

# ─── Step 7: Start Worker v2 ──────────────────────────────────────────────────
step_start_worker_v2() {
  header "Step 8 — Start Worker v2  (build_id = v2.0)"

  section "Open a fourth terminal and run:"
  cmd "cd python
BUILD_ID=v2.0 uv run worker.py" "Terminal 4 — Worker v2"

  echo
  expect "Worker started — deployment=card-service build_id=v2.0"
  echo
  note "Both workers are now running simultaneously — this is a rainbow deployment."
  note "v1.0 continues handling the pinned CardWorkflow execution."
  note "v2.0 is standing by, waiting to be activated."

  echo
  section "Architecture at this point:"
  echo
  diagram "  ┌──────────────────────────────────────────────────┐"
  diagram "  │   Temporal Server                                 │"
  diagram "  │   Deployment: card-service                        │"
  diagram "  │   └─ v1.0  ◄── CURRENT                           │"
  diagram "  │   └─ v2.0      INACTIVE                           │"
  diagram "  └──────────────────────────────────────────────────┘"
  diagram "          ▲                       ▲"
  diagram "  ┌───────────────┐    ┌──────────────────────────┐"
  diagram "  │ Worker v1.0   │    │ Worker v2.0              │"
  diagram "  │ (polling)     │    │ (polling, not yet active)│"
  diagram "  └───────────────┘    └──────────────────────────┘"
  diagram "       card-ACC-001 PINNED ──────┘  (will upgrade at CaN)"

  pause
}

# ─── Step 8: Activate v2 ──────────────────────────────────────────────────────
step_activate_v2() {
  header "Step 9 — Activate v2 as the Current Deployment Version"

  section "Run in any terminal:"
  cmd "temporal worker deployment set-current-version \\
  --deployment-name card-service \\
  --build-id v2.0" "Activate v2"

  echo
  expect "card-service:v2.0 is now the Current version"
  echo
  note "New workflow starts will now go to v2.0."
  note "The existing card-ACC-001 workflow is PINNED — it does NOT migrate yet."
  note "Instead, the SDK sets a flag: target_worker_deployment_version_changed = True."
  note "The workflow will act on this flag at its next CaN boundary."

  section "Verify both versions are tracked:"
  cmd "temporal worker deployment describe --name card-service" "Inspect deployment"

  expect "v1.0 — DRAINING  (pinned workflows still running)"
  expect "v2.0 — CURRENT"

  pause
}

# ─── Step 9: Observe the CaN upgrade ─────────────────────────────────────────
step_observe_upgrade() {
  header "Step 10 — Observe the CaN Upgrade to v2"

  note "Wait for the current 150 s billing cycle to complete on v1."
  note "At cycle end, CardWorkflow checks is_target_worker_deployment_version_changed()."
  note "Since v2 is now current, it calls continue_as_new with AUTO_UPGRADE."
  echo
  section "Watch the worker v1 logs — you should see:"
  echo -e "  ${DIM}  New deployment version available — upgrading at cycle N CaN boundary${NC}"
  echo
  section "Then describe the workflow to confirm the upgrade:"
  cmd "temporal workflow describe -w card-ACC-001" "Confirm upgrade"

  echo
  expect "Versioning Info:"
  expect "  Behavior:  Pinned"
  expect "  Version:   card-service:v2.0"
  expect "  BuildId    v2.0"
  echo
  note "The new run starts on v2.0 with PINNED behavior."

  section "Query pending deployment drainage:"
  cmd "temporal worker deployment describe-version \\
  --deployment-name card-service \\
  --build-id v1.0" "Check v1.0 drainage"

  expect "DrainageStatus: drained  (once card-ACC-001 moved to v2)"
  echo
  note "Once drained, you can safely shut down the v1.0 worker process."
  note "Congratulations! You have completed the PINNED + CaN upgrade demo."

  echo
  section "What just happened — summary:"
  echo
  diagram "  CardWorkflow lifecycle:"
  diagram ""
  diagram "  card-service:v1.0  ──cycle 1──►  generate_statement"
  diagram "                                   rewards += spend * 1"
  diagram "                                   send_notification"
  diagram "                     ──cycle N──►  ... (same)"
  diagram "                                   is_target_version_changed() = True"
  diagram "                                   continue_as_new(AUTO_UPGRADE)"
  diagram "                                        │"
  diagram "                                        ▼"
  diagram "  card-service:v2.0  ──cycle N+1──►  generate_statement"
  diagram "                                     persist_statement  ← NEW"
  diagram "                                     rewards += spend * 1"
  diagram "                                     send_notification  ✓"
  echo

  pause
}

# ─── Run all steps ────────────────────────────────────────────────────────────
main() {
  clear
  echo
  echo -e "${BOLD}${CYAN}"
  echo "  ┌────────────────────────────────────────────────────────────────┐"
  echo "  │      Temporal Worker Versioning Demo                           │"
  echo "  │      Scenario: Credit Card Account — CardWorkflow              │"
  echo "  │                                                                │"
  echo "  │  Concepts covered:                                             │"
  echo "  │    • PINNED versioning behavior                                │"
  echo "  │    • Rainbow deployments                                       │"
  echo "  │    • Upgrade on Continue-as-New                                │"
  echo "  └────────────────────────────────────────────────────────────────┘"
  echo -e "${NC}"
  echo -e "  ${DIM}This guide displays commands to copy into your own terminals.${NC}"
  echo -e "  ${DIM}You will need 4 terminal windows open during the demo.${NC}"
  echo
  read -n 1 -s -r -p "  Press any key to begin..."
  echo -e "\n"

  step_prerequisites
  step_start_server
  step_start_worker_v1
  step_activate_v1
  step_start_workflow
  step_inspect_workflow
  step_update_code
  step_start_worker_v2
  step_activate_v2
  step_observe_upgrade

  clear
  echo
  echo -e "${BOLD}${GREEN}"
  echo "  ┌────────────────────────────────────────────────────────────────┐"
  echo "  │  🎉  Demo Complete!                                            │"
  echo "  │                                                                │"
  echo "  │  You walked through:                                           │"
  echo "  │    ✓  Starting a PINNED CardWorkflow on v1.0                   │"
  echo "  │    ✓  Collecting reward transactions via signals               │"
  echo "  │    ✓  Deploying v2.0 alongside v1.0 (rainbow deploy)          │"
  echo "  │    ✓  Upgrading to v2.0 safely at the CaN boundary            │"
  echo "  │    ✓  Confirming v1.0 drainage with no patching required      │"
  echo "  │                                                                │"
  echo "  │  Next: build TransactionAuthWorkflow (PINNED, short-lived)     │"
  echo "  │         and TransactionDisputeWorkflow (AUTO_UPGRADE)          │"
  echo "  └────────────────────────────────────────────────────────────────┘"
  echo -e "${NC}"
}

main "$@"
