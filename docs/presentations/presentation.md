---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  section {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 1.1rem;
    padding: 48px 64px;
    color: #111827;
  }

  /* ── Title slide ─────────────────────────────────── */
  section.title {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.title h1 {
    color: #f8fafc !important;
    font-size: 2.6rem !important;
    font-weight: 700;
    line-height: 1.2;
    border: none !important;
    margin-bottom: 0.4em;
  }
  section.title p {
    color: #94a3b8 !important;
    font-size: 1.1rem;
    margin: 0;
  }
  section.title .prereq {
    margin-top: 2.5rem;
    background: #1e293b;
    border-left: 3px solid #3b82f6;
    padding: 0.8em 1.2em;
    border-radius: 0 6px 6px 0;
    font-size: 0.95rem;
    color: #cbd5e1 !important;
  }

  /* ── Section divider ─────────────────────────────── */
  section.divider {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.divider h1 {
    color: #f8fafc !important;
    font-size: 2rem !important;
    border: none !important;
    margin-bottom: 0.3em;
  }
  section.divider p {
    color: #93c5fd !important;
    font-size: 1rem;
  }
  section.divider header, section.divider footer,
  section.title header, section.title footer { display: none; }

  /* ── Headings ─────────────────────────────────────── */
  h1 { font-size: 1.6rem; font-weight: 700; color: #111827;
       border-bottom: 2px solid #e5e7eb; padding-bottom: 0.3em; margin-bottom: 0.8em; }
  h2 { font-size: 1.15rem; font-weight: 600; color: #374151; margin-top: 1em; }

  /* ── Badges ───────────────────────────────────────── */
  .badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 4px;
    margin-bottom: 0.6em;
  }
  .concept { background: #dbeafe; color: #1d4ed8; }
  .action  { background: #dcfce7; color: #15803d; }

  /* ── Callout boxes ────────────────────────────────── */
  .note {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 0.6em 1em;
    margin-top: 0.8em;
    border-radius: 0 6px 6px 0;
    font-size: 0.9rem;
  }
  .ok {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    padding: 0.6em 1em;
    margin-top: 0.6em;
    border-radius: 0 6px 6px 0;
    font-size: 0.9rem;
  }
  .danger {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    padding: 0.6em 1em;
    margin-top: 0.6em;
    border-radius: 0 6px 6px 0;
    font-size: 0.9rem;
  }

  /* ── Code ─────────────────────────────────────────── */
  pre {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    border-radius: 8px;
    font-size: 0.82rem;
    line-height: 1.6;
    margin: 0.6em 0;
  }
  code { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
  :not(pre) > code {
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.88em;
  }

  /* ── Tables ───────────────────────────────────────── */
  table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
  th { background: #f1f5f9; font-weight: 600; text-align: left;
       padding: 0.5em 0.8em; border-bottom: 2px solid #e5e7eb; }
  td { padding: 0.45em 0.8em; border-bottom: 1px solid #f1f5f9; }

  /* ── Pagination ───────────────────────────────────── */
  section::after { color: #94a3b8; font-size: 0.8rem; }
---

<!-- _class: title -->
<!-- _backgroundColor: #0f172a -->
<!-- _color: #f8fafc -->

# Temporal Worker Versioning

Deploying code changes to long-running Workflows
without disrupting running digital processes.

<div class="prereq">
<strong>Who this is for:</strong> Teams already running Temporal in production who need
a safe, repeatable strategy for evolving their Workflow code.
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# The Problem

Updating business logic of long-running Workflows is difficult.

---

<span class="badge concept">concept</span>

# [History Replay](https://docs.temporal.io/encyclopedia/event-history/event-history-python#How-History-Replay-Provides-Durable-Execution)

Temporal makes Workflows **Durable**: they survive process crashes, server restarts,
and hardware failures by replaying Workflow History.

```
SDK Worker restart
     │
     ▼
SDK Worker polls Temporal Server for Workflow History Events
     │
     ▼
Worker re-executes Workflow code, command by command
     │
     ▼
Commands must match the recorded Workflow History
```

<div class="note">
Workflow code must be deterministic.

A Workflow is deterministic if every execution of its Workflow Definition produces the same Commands, in the same sequence, given the same input.
</div>

---

<span class="badge concept">concept</span>

# [Non-determinism Error](https://docs.temporal.io/encyclopedia/event-history/event-history-python#Example-of-Non-Deterministic-Workflow)

Adding new Commands (e.g. Activity, Timer, Child Workflow), removing and re-ordering existing Commands may result in Non-determinism Error (NDEs):

```
WARN temporalio_sdk_core::worker::workflow: Failing workflow task run_id=...
failure=Failure { failure: Some(Failure {
    message: "[TMPRL1100] Nondeterminism error: Activity type of scheduled event 'check_fraud' does not match activity type of activity command 'check_credit_limit'",
    source: "", stack_trace: "", encoded_attributes: None, cause: None,
    failure_info: Some(ApplicationFailureInfo(ApplicationFailureInfo {
        r#type: "",
        non_retryable: false,
        details: None,
        next_retry_delay: None,
        category: Unspecified
    })) }),
    force_cause: NonDeterministicError }
```

The Worker expected the sequence of Commands recorded in Event History.
The **new** Workflow code produces a different sequence.
Hence, NDEs are raised.

<div class="danger">
By default, any in-flight Workflow Execution that encounters NDEs will retry indefinitely following exponential backoff.
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# Demo: Credit Card Transaction System

A credit card platform: a mix of short-running and long-running Workflows

---

<span class="badge concept">concept</span>

# The Credit Card Platform

| Workflow | Lifetime | Role |
|---|---|---|
| `CardWorkflow` | months | Entity workflow per card account. Manages billing cycles, rewards, disputes. |
| `TransactionAuthWorkflow` | seconds | One per card swipe. Fraud check → credit check → approve/decline. |
| `TransactionDisputeWorkflow` | days – weeks | One per transactions. Tracks the transaction dispute user journey. |
| `SimulationWorkflow` | continuous | Simulate load: starts card accounts and generate transactions. |

---

<span class="badge concept">concept</span>

# A Transaction Journey

```
SimulationWorkflow  (AUTO_UPGRADE · continuous)
  │
  ├─[once]──► CardWorkflow × 3                          PINNED · months · Continue-as-New
  │           (`card/acc-001`, `card/acc-002`, ...)     billing cycles · rewards · disputes
  │
  └─[loop]──► TransactionAuthWorkflow                   PINNED · seconds
                │  ① check fraud + check credit limit
                │  ② ──signal──► CardWorkflow.record_transaction
                │
                └─[spawn]──► TransactionDisputeWorkflow     AUTO_UPGRADE · days–weeks
                               │  ③ awaits user to initiate dispute (signal)
                               │  ④ notify_merchant
                               │  ⑤ awaits merchant response (signal)
                               │  ⑥ evaluate dispute → finalize dispute
                               └─ ──signal──► CardWorkflow.record_dispute
```

---

<span class="badge action">action</span>

# Start the Temporal Dev Server

Open **Terminal 1** and run:

```bash
temporal server start-dev
```

<div class="ok">
✓  Server listening on  localhost:7233<br>
✓  Web UI available at  http://localhost:8233
</div>

<div class="note">
Leave <strong>Terminal 1</strong> running for the entire session.
</div>

---

<span class="badge action">action</span>

# Start SDK Worker v1

Open **Terminal 2** and run — keep this terminal running:

```bash
mise run worker          # BUILD_ID=v1.0 uv run worker.py
```

<div class="ok">
✓  Worker started — deployment=card-service build_id=v1.0
</div>

<div class="note">
Leave <strong>Terminal 2</strong> running for the entire session.
</div>

---

<span class="badge action">action</span>

# Set the Current Deployment Version

Open **Terminal 3** and activate v1.0 so new Workflow Executions are routed here:

```bash
mise run set-current-version v1.0   # temporal worker deployment set-current-version --deployment-name card-service --build-id v1.0 --yes
```

<div class="ok">
✓  card-service:v1.0 is now the Current version
</div>

---

<span class="badge action">action</span>

# Start the Simulation

In **Terminal 3**, run:

```bash
mise run simulation         # uv run -m workflows.simulation
```

Switch to the Temporal UI and observe:

- `SimulationWorkflow` running continuously
- `CardWorkflow` instances (one per account)
- `TransactionAuthWorkflow` executions completing rapidly
- `TransactionDisputeWorkflow` instances waiting for signals

**This is the live system we will deploy changes to.**

---

<span class="badge action">action</span>

# Run the Replay Tests

In **Terminal 3**, run:

```bash
mise run test               # uv run pytest -v
```

<div class="note">
All tests pass against the current codebase — this is our baseline.
We will revisit Replay tests later to explain how they catch
NDEs <em>before</em> it reaches production.
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# Scenario A

**Business requirement:** reduce fraud API costs by failing fast on credit limit before fraud screening.

Reordering Activity logic in a **short-lived Workflow** (seconds)

---

<span class="badge concept">concept</span>

# Proposed Change in `TransactionAuthWorkflow`

**Request:** run the credit limit check *before* fraud screening to fail fast on the cheaper check and avoid unnecessary fraud API calls.

```python
# v1 — current order
fraud_result  = await workflow.execute_activity(check_fraud, ...)
has_credit    = await workflow.execute_activity(check_credit_limit, ...)
```

```python
# v2 — new order
has_credit    = await workflow.execute_activity(check_credit_limit, ...)
fraud_result  = await workflow.execute_activity(check_fraud, ...)
```

There are in-flight transactions, so this change must be deployed safely.

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# How Would You Approach this New Business Requirement?

Note: `TransactionAuthWorkflow` is a short-lived Workflow that runs for a few seconds.

_Take a moment before proceeding._

---

<span class="badge concept">concept</span>

# Versioning Decision Framework

```
Does the change alter the sequence of Commands the Workflow executes?
│
├── No  (e.g. change Activity logic, update config, add a Signal handler)
│   └── Safe to redeploy — no versioning needed
│
└── Yes  (add, remove, or reorder Activities; change control flow)
       │
       How long does the Workflow run relative to your deploy frequency?
       │
       ├── Short  (completes before the next deploy)
       │   └── PINNED  ·  deploy v2, drain is trivial, no patching
       │
       ├── Long  (weeks – years)  +  uses Continue-as-New
       │   └── PINNED  +  upgrade at CaN boundary  ·  no patching
       │
       └── Medium – Long  +  does NOT use Continue-as-New
           └── AUTO_UPGRADE  +  patching  ·  upgrade at next Workflow Task
```

<div class="note">
Source: <a href="https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#decision-guide">Temporal docs — Worker Versioning Decision Guide</a>
</div>

---

<span class="badge concept">concept</span>

# Decision: Pinned Versioning Behavior

A [**Pinned** Workflow](https://docs.temporal.io/worker-versioning#pinned) is guaranteed to complete on the Worker Deployment Version it started on.

```python
# Declare on the Workflow class — one line, no other changes needed
@workflow.defn(versioning_behavior=VersioningBehavior.PINNED)
class TransactionAuthWorkflow:
    ...
```

Pinned works because the **version boundary aligns with the natural Workflow Execution boundary**, either the end of a short-lived run or a Continue-as-New for long-lived ones.

```
card swipe ──► TransactionAuthWorkflow (v1) ──► done in ~3 s ──┐
                                                                 │
                    v2 deployed & activated                       ▼
                                                            v1 DRAINING
card swipe ──► TransactionAuthWorkflow (v2) ──► done in ~3 s    │
                                                                 ▼
                                                            v1 DRAINED  ✓
```

<div class="note">
Pinned Workflows are designed for <strong>rainbow deployments</strong>: old and new worker
builds run in parallel until the old version drains.
</div>

---

<span class="badge concept">concept</span>

# [Worker Deployments Versions](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#configuring-a-worker-for-versioning)

The Worker announces its version to Temporal Server at startup:

```text
Worker(
    client,
    task_queue="card-task-queue",
    workflows=[CardWorkflow, ...],
    deployment_config=WorkerDeploymentConfig(
        version=WorkerDeploymentVersion(
            deployment_name="card-service",  # logical service name
            build_id="v1.0",                 # this exact code version
        ),
        use_worker_versioning=True,
    ),
)
```

The server uses `deployment_name:build_id` to route each execution to the correct worker.

---

<span class="badge action">action</span>

# Make the v2 Change in `TransactionAuthWorkflow`

Open `python/workflows/transaction_auth.py` and swap the activity order — credit check before fraud:

```python
# TODO (v1): comment out the fraud screening and credit limit check
fraud_result  = await workflow.execute_activity(check_fraud, ...)
has_credit    = await workflow.execute_activity(check_credit_limit, ...)
```

```python
# TODO (v2): uncomment the check_credit_limit and fraud_screening activities
has_credit    = await workflow.execute_activity(check_credit_limit, ...)
fraud_result  = await workflow.execute_activity(check_fraud, ...)
```

---

<span class="badge action">action</span>

# Run the Replay Tests — Observe the Failure

In **Terminal 3**, run:

```bash
mise run test
```

<div class="danger">
tests/test_replay_transaction_auth.py::test_transaction_auth_replay FAILED<br>
<br>
NondeterminismError: Activity type check_credit_limit commanded,<br>
but history has ActivityTaskScheduled for check_fraud.
</div>

The captured Workflow History was recorded with `check_fraud` first.
The v2 code emits Command `check_credit_limit` first.

<div class="note">
Replay tests caught the NDE <strong>before</strong> it reached production.
</div>

---

<span class="badge action">action</span>

# Start Worker v2 alongside v1 — Rainbow Deployment

Open **Terminal 4** and run the v2 Worker (new code, new build ID):

```bash
mise run worker v2.0    # BUILD_ID=v2.0 uv run worker.py
```

<div class="ok">
✓  Worker started — deployment=card-service build_id=v2.0
</div>

Both workers now poll the same task queue simultaneously:

```
┌──────────────────────────────────────────────────┐
│   Temporal Server  ·  card-task-queue            │
└──────────────────────────────────────────────────┘
        ▲                           ▲
┌───────────────┐       ┌───────────────────────────┐
│ Worker v1.0   │       │ Worker v2.0               │
│ (polling)     │       │ (polling, not yet current) │
└───────────────┘       └───────────────────────────┘
 in-flight auths → v1.0      (no new starts yet)
```

---

<span class="badge action">action</span>

# Activate v2 as the Current Deployment Version

In **Terminal 3**, run:

```bash
mise run set-current-version v2.0
```

```bash
# Verify both versions are tracked
temporal worker deployment describe --name card-service
```

<div class="ok">
✓  card-service:v2.0 — CURRENT<br>
✓  card-service:v1.0 — DRAINING  (in-flight auth executions completing)
</div>

<div class="note">
New card swipes are immediately routed to v2.0 (credit check first).<br>
Any in-flight v1.0 auth executions complete in seconds — no intervention needed.
</div>

---

<span class="badge action">action</span>

# Observe New Auth Executions on v2

Watch the Temporal UI or query for recently completed auth executions:

```bash
# Pick a workflow ID and describe it
temporal workflow describe -w transaction/auth/<id>
```

<div class="ok">
✓  Versioning Info:<br>
Behavior: Pinned<br>
Version:  card-service:v2.0
</div>

New auths run `check_credit_limit` first.

---

<span class="badge action">action</span>

# Confirm v1 Drainage

```bash
temporal worker deployment describe --name card-service
```

<div class="ok">
Worker Deployment:<br>
  Name                          card-service<br>
  CurrentVersionDeploymentName  card-service<br>
  CurrentVersionBuildID         v2.0<br>
<br>
Version Summaries:<br>
  DeploymentName  BuildID  DrainageStatus   CreateTime  <br>
  card-service    v2.0     unspecified     2 minutes ago<br>
  card-service    v1.0     draining        4 minutes ago<br>
</div>

`TransactionAuthWorkflow` completes in seconds. It is safe to stop the v1 Worker process (Terminal 2) after v1 is drained.

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# Scenario B

**New business requirement:** persist monthly statements to object storage for compliance.

Add a new Activity to a **long-running Entity Workflow** (which uses Continue-as-New)

---

<span class="badge concept">concept</span>

# Propose Change in `CardWorkflow`

**Request:** persist each billing statement to object storage before sending the notification.

```python
# v1 — current logic during each billing cycle
statement = await workflow.execute_activity(generate_statement, ...)
self.rewards_points += int(statement.total_spend)
await workflow.execute_activity(send_statement_notification, ...)
```

```python
# v2 — what we want to ship
statement = await workflow.execute_activity(generate_statement, ...)
await workflow.execute_activity(persist_statement, ...) # <- NEW ACTIVITY
self.rewards_points += int(statement.total_spend)
await workflow.execute_activity(send_statement_notification, ...)
```

`CardWorkflow` has been running for cycles already, so we cannot simply re-deploy.

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# How Would You Approach this New Business Requirement?

Note: `CardWorkflow` is an Entity Workflow that runs forever. There are in-flight Workflow Executions.

_Take a moment before proceeding._

---

<span class="badge concept">concept</span>

# Versioning Decision Framework

```
Does the change alter the sequence of Commands the Workflow executes?
│
├── No  (e.g. change Activity logic, update config, add a Signal handler)
│   └── Safe to redeploy — no versioning needed
│
└── Yes  (add, remove, or reorder Activities; change control flow)
       │
       How long does the Workflow run relative to your deploy frequency?
       │
       ├── Short  (completes before the next deploy)
       │   └── PINNED  ·  deploy v2, drain is trivial, no patching
       │
       ├── Long  (weeks – years)  +  uses Continue-as-New
       │   └── PINNED  +  upgrade at CaN boundary  ·  no patching
       │
       └── Medium – Long  +  does NOT use Continue-as-New
           └── AUTO_UPGRADE  +  patching  ·  upgrade at next Workflow Task
```

<div class="note">
Source: <a href="https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#decision-guide">Temporal docs — Worker Versioning Decision Guide</a>
</div>

---

<span class="badge concept">concept</span>

# Decision: Pinned Versioning Behavior

A [**Pinned** Workflow]((https://docs.temporal.io/worker-versioning#pinned)) is guaranteed to complete on the Worker Deployment Version, which it started on.

```python
# Declare on the Workflow class — one line, no other changes needed
@workflow.defn(versioning_behavior=VersioningBehavior.PINNED)
class CardWorkflow:
    ...
```

<div class="note">
Pinned Workflows are designed for <strong>rainbow deployments</strong>. Old and new worker
builds run in parallel until the old version drains completely.
</div>

---

<span class="badge concept">concept</span>

# Decision: Upgrade on Continue-as-New (CaN)

By default, a Pinned Workflow stays on its original version even across CaN boundaries. With [Upgrade on CaN]((https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#upgrade-on-continue-as-new)), the **next Workflow Run** may start on the new version.

**How it works:**

1. The current run stays pinned.
2. The Server notifies the Workflow when a new Target Version is available via `is_target_worker_deployment_version_changed()`
3. At the CaN boundary, the Workflow opts in to the upgrade
4. The next run starts on the new version

```python
def _do_continue_as_new(self, account_id: str, cycle: int) -> None:
    if workflow.info().is_target_worker_deployment_version_changed(): # new version available
        workflow.continue_as_new(
            args=[input],
            initial_versioning_behavior=ContinueAsNewVersioningBehavior.AUTO_UPGRADE,
        )  # ← next run lands on the new deployment version; no patching needed
    ...
```

<div class="note">
Sleeping Workflows won't receive the Target-Version-Changed notification
until they execute a Workflow Task. Send a Signal / Update to wake idle Workflows if needed.
</div>

---

<span class="badge concept">concept</span>

# [Worker Deployments Versions](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#configuring-a-worker-for-versioning)

The Worker announces its version to Temporal Server at startup:

```text
Worker(
    client,
    task_queue="card-task-queue",
    workflows=[CardWorkflow, ...],
    deployment_config=WorkerDeploymentConfig(
        version=WorkerDeploymentVersion(
            deployment_name="card-service",  # logical service name
            build_id="v1.0",                 # this exact code version
        ),
        use_worker_versioning=True,
    ),
)
```

The server uses `deployment_name:build_id` to route each execution to the correct worker.

---

<span class="badge action">action</span>

# Add Persist Statement Activity in `CardWorkflow`

Open `python/workflows/card.py` and uncomment the `persist_statement` activity call:

```python
statement = await workflow.execute_activity(generate_statement, ...)

# TODO (v2): store statement in a object storage
await workflow.execute_activity(persist_statement, ...)

self.rewards_points += int(statement.total_spend)
```

---

<span class="badge action">action</span>

# Run the Replay Tests — Observe the Failure

In **Terminal 3**, run:

```bash
mise run test
```

<div class="danger">
tests/test_replay_card.py::test_card_workflow_replay_after_can FAILED     [ 33%]<br>
<br>
FAILED tests/test_replay_card.py::test_card_workflow_replay_after_can - temporalio.workflow.NondeterminismError: Workflow activation completion fail...
</div>

The captured Workflow Histories were recorded **without** `persist_statement`.
The new code now produces a **different Command sequence**. Hence, Replay fails.

<div class="note">
Replay tests help catch NDEs <strong>before</strong> they reach production.
This is why we need to version this change.
</div>

---

<span class="badge action">action</span>

# Start Worker v3 alongside v2 — Rainbow Deployment

Open a new terminal and run the v3 Worker (new code, new build ID). Worker v1 is already drained and decommissioned.

```bash
mise run worker v3.0    # BUILD_ID=v3.0 uv run worker.py
```

<div class="ok">
✓  INFO:root:Worker started — deployment=card-service build_id=v3.0 task_queue=card-task-queue address=localhost:7233
</div>

```
┌──────────────────────────────────────────────────┐
│   Temporal Server  ·  card-task-queue            │
└──────────────────────────────────────────────────┘
        ▲                           ▲
┌───────────────┐       ┌───────────────────────────┐
│ Worker v2.0   │       │ Worker v3.0               │
│ (polling,     │       │ (polling, not yet current) │
│  CURRENT)     │       │                            │
└───────────────┘       └───────────────────────────┘
 card/acc-* → v2.0           (no new starts yet)
```

<div class="note">
Worker v1.0 is already <strong>drained and decommissioned</strong>. Only v2 and v3 are active.
</div>

---

<span class="badge action">action</span>

# Activate v3 as the Current Deployment Version

```bash
mise run set-current-version v3.0
```

```bash
# Verify all tracked versions
temporal worker deployment describe --name card-service
```

<div class="ok">
✓  card-service:v3.0 — unspecified<br>
✓  card-service:v2.0 — DRAINING  (pinned CardWorkflow executions awaiting CaN)<br>
✓  card-service:v1.0 — DRAINED   (decommissioned)
</div>

<div class="note">
New Workflow Executions start on v3.0.<br>
Existing Pinned executions (card/acc-*) stay on v2.0 until they reach a CaN boundary.
</div>

---

<span class="badge action">action</span>

# Observe the CaN Upgrade to v3

Wait for the billing cycle to complete (~30 s). Watch the v2 Worker logs:

```
INFO  New deployment version available — upgrading at cycle N CaN boundary
```

Then confirm the new run is on v3 through the Web UI.

The same Workflow ID — new run, new build, new business logic. No patching.

---

<span class="badge action">action</span>

# Confirm v2 Drainage and Decommission the v2 Worker

```bash
temporal worker deployment describe --name card-service
```

<div class="ok">
card-service    v2.0     drained         11 minutes ago
</div>

Once drained, stop the v2 Worker process. The deployment state is now:

```
Worker Deployment:
  Name                          card-service
  CurrentVersionDeploymentName  card-service
  CurrentVersionBuildID         v3.0

Version Summaries:
  DeploymentName  BuildID  DrainageStatus    CreateTime
  card-service    v3.0     unspecified     3 minutes ago
  card-service    v2.0     drained         11 minutes ago
  card-service    v1.0     drained         12 minutes ago
```

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# Scenario C

**Business requirement:** issue provisional credit immediately when a customer initiates a dispute.

Adding a new Activity mid-execution to a **medium-lived Workflow** (days to weeks)

---

<span class="badge concept">concept</span>

# Proposed Change in `TransactionDisputeWorkflow`

**Request:** issue provisional credit to the cardholder immediately after they submit a dispute.

```python
# v1 — current logic after cardholder confirms
await workflow.wait_condition(lambda: self._submitted, timeout=SUBMISSION_TIMEOUT)

await workflow.execute_activity(notify_merchant, ...)
```

```python
# v2 — add provisional credit between submission and merchant notification
await workflow.wait_condition(lambda: self._submitted, timeout=SUBMISSION_TIMEOUT)

await workflow.execute_activity(issue_provisional_credit, ...)  # ← NEW

await workflow.execute_activity(notify_merchant, ...)
```

Dispute Workflows can run for **days or weeks**. There may be hundreds in-flight when we deploy.

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# How Would You Approach This New Business Requirement?

Note: `TransactionDisputeWorkflow` is a medium-lived Workflow. There are in-flight Workflow Executions that may be waiting for a dispute initiation for up to 30 days.

_Take a moment before proceeding._

---

<span class="badge concept">concept</span>

# Versioning Decision Framework

```
Does the change alter the sequence of Commands the Workflow executes?
│
├── No  (e.g. change Activity logic, update config, add a Signal handler)
│   └── Safe to redeploy — no versioning needed
│
└── Yes  (add, remove, or reorder Activities; change control flow)
       │
       How long does the Workflow run relative to your deploy frequency?
       │
       ├── Short  (completes before the next deploy)
       │   └── PINNED  ·  deploy vNext, drain is trivial, no patching
       │
       ├── Long  (weeks – years)  +  uses Continue-as-New
       │   └── PINNED  +  upgrade at CaN boundary  ·  no patching
       │
       └── Medium – Long  +  does NOT use Continue-as-New      ← we are here
           └── AUTO_UPGRADE  +  workflow.patched()  ·  upgrade at next Workflow Task
```

<div class="note">
Source: <a href="https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#decision-guide">Temporal docs — Worker Versioning Decision Guide</a>
</div>

---

<span class="badge concept">concept</span>

# Decision: Auto-upgrade + `workflow.patched()`

`TransactionDisputeWorkflow` runs for days and it doesn't use CaN. We need in-flight executions to pick up new code at their **next Workflow Task**.

```text
@workflow.defn(versioning_behavior=VersioningBehavior.AUTO_UPGRADE)
class TransactionDisputeWorkflow:
    ...
```

<div class="note">
Auto-upgrade Workflow requires Workflow patching.
</div>

---

<span class="badge concept">concept</span>

# [Patching](https://docs.temporal.io/patching)

`workflow.patched()` writes a **Marker event** to Workflow History the first time it runs, then reads that Marker on subsequent replays:

```python
# v4 — safe to deploy to in-flight executions
if workflow.patched("add-provisional-credit"):
    await workflow.execute_activity(
        issue_provisional_credit,
        ...
    )
```

| Execution | `workflow.patched()` returns | Behaviour |
|---|---|---|
| Started on v3, upgraded to v4 | `False` (no marker in history) | skips the block |
| Started on v4 | `True` (marker written) | executes the block |

Once **all** pre-patch executions complete, the patch can be [deprecated](https://docs.temporal.io/develop/python/workflows/versioning#deprecated-patches).

---

<span class="badge action">action</span>

# Make the v4 Change in `TransactionDisputeWorkflow`

Open `python/workflows/transaction_dispute.py` and uncomment the `workflow.patched()` block:

```text
# v4 — uncomment this block
if workflow.patched("add-provisional-credit"):
    await workflow.execute_activity(
        issue_provisional_credit,
        args=[request.card_id, request.amount],
        start_to_close_timeout=timedelta(seconds=10),
    )
```

---

<span class="badge action">action</span>

# Run the Replay Tests — Confirm They Pass

In **Terminal 3**, run:

```bash
mise run test
```

<div class="ok">
✓  test_transaction_dispute_replay PASSED<br>
✓  test_transaction_dispute_replay_merchant_no_response PASSED<br>
✓  test_transaction_dispute_replay_unauthorized PASSED<br>
<br>
All dispute replay tests pass.
</div>

`workflow.patched()` returns `False` for histories that predate the change. The new Activity is skipped on replay. The change is safe to deploy.

<div class="note">
This is what distinguishes AUTO_UPGRADE + <code>patched()</code> from a naive code change: the patch helpguard against NDEs.
</div>

---

<span class="badge action">action</span>

# Start Worker v4 alongside v3 — Rainbow Deployment

Open **Terminal 4** and run the v4 Worker. Worker v1 and v2 are already drained and decommissioned.

```bash
mise run worker v4.0    # BUILD_ID=v4.0 uv run worker.py
```

<div class="ok">
✓  Worker started — deployment=card-service build_id=v4.0
</div>

```
┌──────────────────────────────────────────────────┐
│   Temporal Server  ·  card-task-queue            │
└──────────────────────────────────────────────────┘
        ▲                           ▲
┌───────────────┐       ┌───────────────────────────┐
│ Worker v3.0   │       │ Worker v4.0               │
│ (polling,     │       │ (polling, not yet current) │
│  CURRENT)     │       │                            │
└───────────────┘       └───────────────────────────┘
 in-flight disputes → v3.0   (no new starts yet)
```

---

<span class="badge action">action</span>

# Activate v4 as the Current Deployment Version

In **Terminal 3**, run:

```bash
mise run set-current-version v4.0
```

```bash
temporal worker deployment describe --name card-service
```

<div class="ok">
✓  card-service:v4.0 — unspecified<br>
✓  card-service:v3.0 — DRAINING  (in-flight AUTO_UPGRADE disputes now served by v4)<br>
✓  card-service:v2.0 — DRAINED   (decommissioned)<br>
✓  card-service:v1.0 — DRAINED   (decommissioned)
</div>

<div class="note">
AUTO_UPGRADE disputes migrate to v4 at their <strong>next Workflow Task</strong> — no signals or CaN needed.
</div>

---

<span class="badge action">action</span>

# Observe Old and New Disputes Diverging

Signal an in-flight dispute (started on v3) and describe a newly started dispute:

```text
# Signal an in-flight dispute — it will run on v4 at its next Workflow Task
temporal workflow signal --workflow-id <existing-dispute-id> \
  --name submit_dispute --input '"unauthorized"'

# Describe a newly started dispute
temporal workflow describe -w <new-dispute-id>
```

<div class="ok">
✓  In-flight dispute (v3 history):  skips provisional credit  (no patch marker)<br>
✓  New dispute (v4):                issues provisional credit  (patch marker written)
</div>

Both executions are deterministic. Both are correct for their version of history.

---

<span class="badge action">action</span>

# Confirm v3 Drainage

```bash
temporal worker deployment describe-version \
  --deployment-name card-service \
  --build-id v3.0
```

<div class="ok">
✓  DrainageStatus: drained
</div>

Once v3 is drained, all disputes have either completed or started fresh on v4. The patch guard (`workflow.patched("add-provisional-credit")`) can be deprecated in the next deploy.

```
card-service:v4.0 — CURRENT   (all new and upgraded executions)
card-service:v3.0 — DRAINED   (safe to decommission; remove patch guard in v5)
card-service:v2.0 — DRAINED   (already decommissioned)
card-service:v1.0 — DRAINED   (already decommissioned)
```

---

<!-- _class: divider -->
<!-- _paginate: false -->
<!-- _backgroundColor: #1e3a5f -->
<!-- _color: #f8fafc -->

# Recap

Choosing the right Worker Versioning strategy for your Workflows

---

<span class="badge concept">concept</span>

# Decision Guide

From the [Temporal Worker Versioning Decision Guide](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning#decision-guide):

| Workflow Duration | Uses Continue-as-New? | Recommended Behavior | Patching Required? | This session |
|---|---|---|---|---|
| **Short** (completes before next deploy) | N/A | `PINNED` | Never | Scenario A · `TransactionAuthWorkflow` |
| **Medium** (spans multiple deploys) | No | `AUTO_UPGRADE` | Yes | Scenario C · `TransactionDisputeWorkflow` |
| **Long** (weeks to years) | Yes | `PINNED` + upgrade on CaN | Never | Scenario B · `CardWorkflow` |
| **Long** (weeks to years) | No | `AUTO_UPGRADE` + patching | Yes | — |

Both strategies require **rainbow deployments**: old and new workers running in parallel until the old build is fully drained.

---

<span class="badge concept">concept</span>

# Operational checklist to take home

**Replay tests**
Export Workflow Histories from production and run Replay tests in CI against every new build. A `NondeterminismError` in CI means the change is unsafe and requires versioning.

**Build ID**
Use a consistent, human-readable convention: `<service-name>:<semver>` (e.g. `card-service:v2.1.0`) or `<service-name>:<git-sha>` for continuous delivery pipelines. The build ID is permanent — once recorded in a Workflow's history it cannot be changed.

**Automation**
For teams running on Kubernetes, the [Temporal Worker Controller](https://docs.temporal.io/production-deployment/worker-deployments/kubernetes-controller) automates rainbow deployments: it manages version activation, drain monitoring, and worker shutdown without manual CLI steps. Use it to reduce the operational burden of managing multiple active versions.
