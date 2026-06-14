.. _job-chaining:

Job Chaining — Passing Data Between Jobs
=========================================

**Target Audience:** Developers, Advanced Users
**Difficulty:** Advanced
**Prerequisites:** :doc:`data-model`, :doc:`job-lifecycle`, :doc:`execution-architecture`

.. contents::
   :local:
   :depth: 2

Overview
--------

Job chaining lets the output produced by one job (the **producer**, run-template A)
become the input of another job (the **consumer**, run-template B). You wire
run-templates into pipelines without writing custom glue code.

Two delivery modes are available:

- **Whole-file delivery** — A produces a JSON file; B receives the path to that
  file via an environment variable bound to a command-line switch.
- **Item-level mapping** — Individual scalar values extracted from A's produced
  JSON are routed into individual environment variables for B's command.

A and B may come from **different providers**, so output field names on the two
sides will generally not match. You describe the cross-provider field pairing in
a *binding* (an ``event_rule`` row) that the server applies at chain-execution
time. The primary execution path is the internal event-rule processor
(``eventrules.php``). A graphical editor for bindings is provided by the
Node-RED ``multiflexi-map`` node.

The data model for a chain is:

.. code-block:: text

   RunTemplate A  ──produces──►  Binding (EventRule)  ──env override──►  RunTemplate B
                                     env_mapping JSON

App Contract
------------

Both the producer and the consumer declare their data interface in the
``*.app.json`` definition. MultiFlexi imports and persists these declarations so
the binding editor can list available fields.

``produces`` — Producer side
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``produces`` block describes each named output your app generates. Provide one
entry per distinct output artifact.

.. code-block:: json

   "produces": {
     "invoices": {
       "format": "json",
       "description": { "en": "Issued invoices", "cs": "Vystavené faktury" },
       "patterns": ["invoices-[0-9]+\\.json"],
       "fields": {
         "invoice_number": {
           "type": "string",
           "description": { "en": "Invoice number" }
         },
         "total": {
           "type": "float",
           "description": { "en": "Total amount" }
         },
         "customer_id": {
           "type": "integer",
           "path": "$.customer.id"
         }
       }
     }
   }

Key fields:

- **format** — one of ``file``, ``json``, ``text``, ``url``, ``custom``.
- **patterns** — list of regex patterns used to locate the produced file among
  job artifacts (matched against filenames in the temp directory).
- **fields** — optional metadata describing individual items inside a JSON
  output. Each entry may carry a **path** property (JSONPath) for nested values.
  These field names are what you reference on the left side of a binding
  selector.

``consumes`` — Consumer side
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``consumes`` block binds incoming data to the existing ``environment`` keys
that already drive the app's command line. Use your ``environment`` block as the
single source of truth for what the command accepts; ``consumes`` just annotates
which of those keys can be fed from a chain.

.. code-block:: json

   "environment": {
     "INPUT_FILE": {
       "type": "file-path",
       "category": "Behavior",
       "description": { "en": "Input JSON file" },
       "required": true
     },
     "MIN_AMOUNT": {
       "type": "float",
       "description": { "en": "Minimum amount to process" }
     }
   },
   "cmdparamsTemplate": "--input {INPUT_FILE} --min {MIN_AMOUNT}",

   "consumes": {
     "source": {
       "format": "json",
       "description": { "en": "Invoices to process" },
       "required": true,
       "target": "INPUT_FILE",
       "fields": {
         "amount_threshold": {
           "target": "MIN_AMOUNT",
           "format": "float"
         }
       }
     }
   }

Key fields:

- **target** — the ``environment`` key that receives the produced artifact's
  file path (whole-file delivery mode).
- **fields[*].target** — the ``environment`` key that receives a single
  extracted scalar (item-level mapping mode).

The same ``consumes`` declaration covers both delivery modes: ``target`` for
whole-file and ``fields[*].target`` for per-item.

Full Producer–Consumer Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below is a side-by-side example showing an invoice-export app (producer) and an
invoice-processing app (consumer).

Producer — ``invoice-export.app.json`` (excerpt):

.. code-block:: json

   {
     "uuid": "aaaaaaaa-0001-0000-0000-000000000001",
     "executable": "invoice-export",
     "environment": {
       "RESULT_FILE": {
         "type": "string",
         "defval": "invoices-result.json",
         "description": { "en": "Output file for produced invoices" },
         "required": false,
         "category": "Other"
       }
     },
     "produces": {
       "invoices": {
         "format": "json",
         "description": { "en": "Issued invoices" },
         "patterns": ["invoices-.*\\.json$"],
         "fields": {
           "invoice_number": { "type": "string" },
           "total":          { "type": "float"  },
           "customer_id":    { "type": "integer", "path": "$.customer.id" }
         }
       }
     }
   }

Consumer — ``invoice-processor.app.json`` (excerpt):

.. code-block:: json

   {
     "uuid": "bbbbbbbb-0002-0000-0000-000000000002",
     "executable": "invoice-processor",
     "environment": {
       "INPUT_FILE": {
         "type": "file-path",
         "category": "Behavior",
         "description": { "en": "Path to invoice JSON file" },
         "required": true
       },
       "MIN_AMOUNT": {
         "type": "float",
         "description": { "en": "Minimum invoice amount to process" }
       }
     },
     "cmdparamsTemplate": "--input {INPUT_FILE} --min {MIN_AMOUNT}",
     "consumes": {
       "source": {
         "format": "json",
         "description": { "en": "Invoices produced by invoice-export" },
         "required": true,
         "target": "INPUT_FILE",
         "fields": {
           "amount_threshold": {
             "target": "MIN_AMOUNT",
             "format": "float"
           }
         }
       }
     }
   }

See :doc:`../apps_development` for the full application definition schema and how
to validate your JSON.

Selector Syntax
---------------

A selector is the value side of an ``env_mapping`` entry. It tells the runtime
how to extract data from A's produced output.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Selector form
     - Description
   * - ``invoices.total``
     - Dot-path: extract the scalar at key ``total`` inside A's produced JSON
       named ``invoices``.
   * - ``$.customer.id``
     - JSONPath: extract a nested value. The ``$`` prefix activates JSONPath
       mode; nested traversal uses dot notation.
   * - ``invoices.customer.id``
     - Multi-level dot-path: equivalent to ``$.customer.id`` when the produced
       JSON root is ``invoices``.
   * - ``@file:invoices``
     - Whole-file: materialize A's ``invoices`` produced artifact to a temporary
       file and pass the **path** of that file as the env value. Use this to
       satisfy a consumer ``environment`` key of type ``file-path``.

.. note::

   The ``@file:`` selector writes the artifact content to a temporary path at
   chain-execution time. The consumer receives the path string, not the file
   content. Clean-up of these temporary files is the responsibility of the
   executor environment; see :ref:`chaining-caveats` for details.

Binding Configuration (``event_rule.env_mapping``)
---------------------------------------------------

Bindings are stored as rows in the ``event_rule`` table. The ``env_mapping``
column holds a JSON object where:

- **keys** are the consumer's (B's) ``environment`` variable names.
- **values** are selectors addressing a piece of A's produced output.

Example binding for the producer–consumer pair above:

.. code-block:: json

   {
     "INPUT_FILE": "@file:invoices",
     "MIN_AMOUNT": "invoices.total"
   }

This mapping tells MultiFlexi: when run-template A completes, write A's
``invoices`` artifact to a temp path and set ``INPUT_FILE`` to that path, then
extract the ``total`` field from the ``invoices`` JSON and set ``MIN_AMOUNT`` to
that value. Run-template B is then launched with these env overrides, so
``invoice-processor --input /tmp/chain-xyz.json --min 1500.00`` is the resulting
command.

You manage bindings through:

- **Node-RED** ``multiflexi-map`` node (recommended for visual editing — see below).
- **CLI** ``multiflexi-cli event-rule:create`` / ``event-rule:update`` for scripted
  management.
- **REST API** ``POST /api/.../event-rule/`` for programmatic setup.

Runtime Data Flow
-----------------

The following steps happen each time a chained producer job completes:

1. **Job A finishes.** ``eventrules.php`` receives the ``job.completed`` event
   for run-template A.
2. **Bindings are loaded.** The processor queries all ``event_rule`` rows whose
   trigger is the completion of run-template A.
3. **Produced data is collected.** ``Job::collectProducedData()`` reads A's
   artifacts and decodes JSON outputs into an in-memory associative array.
4. **Selector resolution runs** for each entry in ``env_mapping``:

   - ``@file:<name>`` — the named artifact is written to a temporary file; the
     value becomes the temp file path.
   - dot-path / JSONPath — the scalar is extracted from A's decoded produced JSON.

5. **An env override is built.** The resolved ``{ ENV_KEY: value }`` pairs form
   a ``ConfigFields`` override identical to what the executor accepts via the
   ``-E`` flag.
6. **Job B is scheduled.** ``eventrules.php`` calls
   ``Job::prepareJob(RunTemplate B, $override, now(), ...)`` so B runs
   immediately with A's data injected as environment variables.
7. **B's command is rendered.** ``Job::getCmdParams()`` substitutes
   ``{INPUT_FILE}`` and ``{MIN_AMOUNT}`` placeholders in
   ``cmdparamsTemplate``, producing the final command line.

.. code-block:: text

   [ Job A ]
       │  produces invoices.json
       ▼
   [ eventrules.php ]
       │  resolves env_mapping selectors
       ▼
   [ ConfigFields override:  INPUT_FILE=/tmp/..., MIN_AMOUNT=1500.00 ]
       │
       ▼
   [ Job B ]  invoice-processor --input /tmp/chain-xyz.json --min 1500.00

Node-RED: ``multiflexi-map`` Node
----------------------------------

The ``multiflexi-map`` node in ``node-red-contrib-multiflexi`` provides a visual
binding editor. It operates in two modes.

**Server-backed mode (default)**

The node creates or updates an ``event_rule`` row via the REST API and keeps its
``id``. The same binding then applies whether the chain is triggered from Node-RED
or by the internal ``eventrules.php`` processor.

The editor shows two columns:

- **Left** — A's ``produces.*.fields`` (plus a "whole file" option for each
  produce block).
- **Right** — B's ``consumes`` and ``environment`` keys.

You pair items by dragging a line from a left entry to a right entry. The node
saves the resulting ``env_mapping`` JSON to the server-side ``event_rule``.

**Local transform mode**

When you do not want a server-side rule for a given flow, the node converts
``msg.payload`` from A's output directly into ``msg.payload.env`` for the
downstream ``multiflexi-runtemplate`` node, which already merges
``msg.payload.env`` into the job env at launch time. This mode does not touch
the ``event_rule`` table.

See the ``node-red-contrib-multiflexi`` README for installation and detailed
node configuration.

.. _chaining-caveats:

Constraints and Caveats
------------------------

**Array fan-out is not supported in v1.**
If A produces a JSON *array* of records (rather than an object), use whole-file
mode (``@file:<name>``). Per-record fan-out — spawning one consumer job per
array element — is deferred to a future release.

**Temporary file lifecycle.**
Files materialized by ``@file:`` selectors are written to the executor's temp
directory. They persist for the duration of job B's execution. MultiFlexi does
not delete them automatically after B finishes; rely on the executor environment's
normal temp-file cleanup (e.g. ``/tmp`` on systemd systems with
``PrivateTmp=true``) or have consumer B delete the file after reading it.

**Idempotency is an app-level concern.**
If a retry causes job A to run more than once in the same window, the downstream
chain fires once per successful A completion. Consumer apps must handle duplicate
inputs (e.g. by checking whether the invoice was already imported before
processing it again).

**Manual jobs trigger the chain.**
A manually triggered job that completes successfully fires the same
``job.completed`` event and will trigger all bindings attached to that
run-template.

**Backfill is not defined.**
When the scheduler daemon was down and several windows of A were missed, only
windows where A's job actually ran will trigger consumer jobs. Missed windows do
not cause retroactive chain executions.

See Also
--------

- :doc:`../apps_development` — how to add ``produces`` / ``consumes`` blocks to
  your application JSON definition.
- :doc:`../commandline` — ``multiflexi-executor`` flags for injecting env
  overrides (``-E``, ``--env-json``).
- :doc:`data-model` — job and event-rule entity relationships.
- :doc:`job-lifecycle` — how a job progresses from creation to completion.
- :doc:`tasks` — Task-level SLA tracking over multiple job attempts.
