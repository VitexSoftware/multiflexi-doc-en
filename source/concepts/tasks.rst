Tasks
=====

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

MultiFlexi introduces the **Task** concept to answer a question that Jobs alone cannot: *"was the periodic obligation actually fulfilled within its window?"*

A Task is the unit of obligation for one scheduling window. A Job is a single attempt at fulfilling it. When a RunTemplate has an hourly interval, 24 Tasks are produced per day. Each Task is fulfilled by the first successful Job. If a Job fails, retry Jobs are spawned within the same window until one succeeds or the budget is exhausted.

Headline metric: ``23/24 tasks fulfilled on time, 1 late`` instead of raw job counts.

Data Model
----------

.. code-block:: text

   RunTemplate  1 ── N  Task  1 ── N  Job

- **RunTemplate** — unchanged role; gains retry and SLA configuration fields.
- **Task** — one scheduling window. Holds 1..N Jobs. Fulfilled when one succeeds.
- **Job** — one execution attempt. Gains a ``task_id`` foreign key.

Task States
-----------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - State
     - Meaning
   * - ``open``
     - Window open, no successful job yet.
   * - ``running``
     - A job is currently executing.
   * - ``fulfilled``
     - A job succeeded on or before the deadline.
   * - ``fulfilled_late``
     - A job succeeded after the deadline but within the window (requires ``allow_late = true``).
   * - ``failed``
     - The retry budget was exhausted or the window expired without a successful job.
   * - ``missed``
     - The window expired with zero job attempts (scheduler was down).

State Machine
~~~~~~~~~~~~~

.. code-block:: text

   open
   ├─► running ──► fulfilled          (success ≤ deadline)
   │           ──► fulfilled_late     (deadline < success ≤ window_end, allow_late=true)
   │           ──► open               (job failed, retry budget remains)
   │           ──► failed             (budget exhausted or window expired)
   └─► missed                         (window_end reached, zero attempts)

Cadence vs Deadline
-------------------

A periodic obligation has two independent time anchors:

- **Cadence (interval)** — how often a new Task is born. Defines Task *identity*.
- **Deadline (SLA)** — by when the result must be ready to be *useful*. Defaults to the window end, can be set earlier.

Example — daily bank-statement download with an 08:00 deadline:

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Scenario
     - Window
     - Deadline
     - Retry budget
   * - Minute interval
     - 1 min
     - = window end
     - ~0 (no real retry)
   * - Hourly interval
     - 1 h
     - = window end
     - 60 min → 4–8 tries
   * - Daily, morning
     - 24 h
     - e.g. 08:00
     - 08:00 − window start

RunTemplate Retry/SLA Configuration
------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Default
     - Description
   * - ``deadline_offset``
     - null
     - Offset from window start (``+3h``) or absolute time-of-day (``08:00``). ``null`` = window end.
   * - ``max_attempts``
     - 1
     - Maximum number of job attempts per task window.
   * - ``retry_backoff``
     - ``none``
     - Strategy: ``none`` | ``fixed`` | ``linear`` | ``exponential``.
   * - ``retry_min_gap``
     - 0
     - Minimum seconds between retry attempts.
   * - ``allow_late``
     - false
     - Whether a post-deadline success counts as ``fulfilled_late``.

If ``retry_min_gap × max_attempts > (deadline − window_start)``, the scheduler caps ``max_attempts`` and emits a warning.

REST API
--------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Endpoint
     - Description
   * - ``GET /tasks.json``
     - List tasks. Query params: ``state``, ``runtemplate_id``, ``from``, ``to``, ``limit``.
   * - ``GET /task/{id}.json``
     - Single task with embedded ``jobs`` array (attempt history).

The existing ``GET /job/{id}.json`` response now includes a ``task_id`` field.

CLI Commands
------------

task:list
~~~~~~~~~

List tasks::

   multiflexi-cli task:list [options]

Options:

.. list-table::
   :header-rows: 1

   * - Option
     - Description
   * - ``--runtemplate=ID``
     - Filter by RunTemplate ID
   * - ``--state=STATE``
     - Filter by state (open, running, fulfilled, …)
   * - ``--from=DATETIME``
     - Window start from
   * - ``--to=DATETIME``
     - Window end to
   * - ``--limit=N``
     - Limit results (default 50)
   * - ``--format=text|json``
     - Output format

task:get
~~~~~~~~

Get a single task with its job history::

   multiflexi-cli task:get --id=42
   multiflexi-cli task:get --id=42 --format=json

See Also
--------

- :doc:`job-lifecycle` — Job state transitions
- :doc:`execution-architecture` — How the scheduler daemon works
