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

# Temporal Workflow Versioning

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
Leave *Terminal 1* running for the entire session.
</div>

---

<span class="badge action">action</span>

# Start SDK Worker v1 and Set the Current Version

Open **Terminal 2** and run — keep this terminal running:

```bash
mise run worker:v1          # BUILD_ID=v1.0 uv run worker.py
```

<div class="note">
Leave *Terminal 2* running for the entire session.
</div>

Open **Terminal 3** and activate the Deployment Version so new Workflow Executions are routed here:

```bash
mise run set-current-version v1.0   # temporal worker deployment set-current-version --deployment-name card-service --build-id v1.0 --yes
```

<div class="ok">
✓  Worker started — deployment=card-service build_id=v1.0<br>
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
