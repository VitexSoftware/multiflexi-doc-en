Node-RED Integration
====================

MultiFlexi integrates with `Node-RED <https://nodered.org/>`_ to provide a
visual interface for managing relationships between MultiFlexi processes. Events
flowing through MultiFlexi (incoming webhooks and finished jobs) are forwarded to
Node-RED, where flows decide which RunTemplates to schedule. The arrows you draw
in Node-RED become the orchestration logic between your processes.

.. toctree::
   :maxdepth: 2

.. contents::
   :local:
   :depth: 3

Overview
--------

The integration turns the ``multiflexi-eventor`` daemon into a bidirectional
bridge:

- **Outbound** — the daemon forwards two kinds of events to a Node-RED HTTP-in
  endpoint as JSON: webhook changes (from adapter ``changes_cache`` tables) and
  finished jobs (with produced artifact metadata).
- **Inbound** — Node-RED schedules RunTemplates by calling the MultiFlexi REST
  API (``POST /job/``).

Two common patterns:

1. **Event to action.** A payment-received webhook arrives → an arrow in
   Node-RED → schedule the *Payment Receipt Confirmation* RunTemplate.
2. **Output chaining.** A RunTemplate produces a JSON artifact → an arrow in
   Node-RED → schedule a data-consumer RunTemplate, forming a processing chain.

Architecture
------------

.. code-block:: text

   abraflexi-webhook-acceptor → changes_cache
              │ (poll)
     multiflexi-eventor ──HTTP POST──▶ [multiflexi-event] ─▶ [multiflexi-runtemplate] ──HTTP──▶ MultiFlexi API
              │ (poll finished jobs)
              └────────────HTTP POST──▶ [multiflexi-event:job.completed] ─▶ [multiflexi-artifact] ─▶ [multiflexi-runtemplate]

The bridge is implemented in ``multiflexi-event-processor``:

- ``NodeRedBridge`` — performs the cURL POST of normalized event JSON.
- ``EventProcessor`` — forwards each incoming webhook change when forwarding is
  enabled.
- ``JobWatcher`` — polls the ``job`` table for newly finished jobs and forwards a
  ``job.completed`` event (with artifact metadata), tracking a persistent
  high-water mark so restarts do not replay history.

Prerequisites
-------------

Before you start, make sure you have:

- A running **MultiFlexi** instance whose REST API is reachable from the
  Node-RED host. The API base URL ends with the version path, for example
  ``http://multiflexi.example.com/api/VitexSoftware/MultiFlexi/1.0.0``.
- The **multiflexi-eventor** daemon (``multiflexi-eventor`` package) installed and
  pointed at the same database as the executor and scheduler.
- A running **Node-RED** instance (version 4.0 or newer recommended).
- At least one **RunTemplate** you want to trigger, and its numeric ID.

Installing the Node-RED nodes
-----------------------------

The nodes ship as the ``node-red-contrib-multiflexi`` package (in the
``nodered/`` directory of the ``multiflexi-event-processor`` repository).

**Debian package (recommended)** installs the nodes to
``/usr/share/nodejs/node-red-contrib-multiflexi``:

.. code-block:: bash

   sudo apt install node-red-contrib-multiflexi
   sudo systemctl restart node-red

**From source**, install into the Node-RED user directory and restart:

.. code-block:: bash

   cd ~/.node-red
   npm install /path/to/multiflexi-event-processor/nodered
   sudo systemctl restart node-red

After the restart, the four **MultiFlexi** nodes appear in the editor palette.
Confirm they registered without errors:

.. code-block:: bash

   # node-red writes its node registry here (userDir/.config.nodes.json)
   grep -A2 node-red-contrib-multiflexi ~/.node-red/.config.nodes.json

Each node set should show ``"enabled": true`` and no ``"err"`` value.

Configuring the eventor daemon
------------------------------

Set the following keys in ``/etc/multiflexi/multiflexi.env`` (production) or the
project ``.env`` (development), then restart the daemon. Leave
``NODERED_WEBHOOK_URL`` empty to disable the bridge entirely.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Key
     - Description
   * - ``NODERED_WEBHOOK_URL``
     - Target Node-RED HTTP-in URL (matches the **HTTP Path** of a
       ``multiflexi-event`` node). Empty disables forwarding.
   * - ``NODERED_TOKEN``
     - Optional shared secret sent as the ``X-MultiFlexi-Token`` header.
   * - ``NODERED_TIMEOUT``
     - HTTP request timeout in seconds (default ``5``).
   * - ``NODERED_FORWARD_CHANGES``
     - Forward incoming webhook changes (default ``true`` when a URL is set).
   * - ``NODERED_JOB_STATE_FILE``
     - Path to the persisted last-forwarded job id (default
       ``/var/lib/multiflexi-eventor/last_forwarded_job``).
   * - ``MULTIFLEXI_EVENT_BATCH``
     - Maximum webhook changes processed per cycle (default ``100``).
   * - ``MULTIFLEXI_JOB_BATCH``
     - Maximum finished jobs forwarded per cycle (default ``100``).

.. code-block:: ini

   NODERED_WEBHOOK_URL=http://node-red.example.com:1880/multiflexi-event
   NODERED_FORWARD_CHANGES=true
   NODERED_TOKEN=change-me

.. code-block:: bash

   sudo systemctl restart multiflexi-eventor

.. note::

   The ``/multiflexi-event`` HTTP route only exists once a ``multiflexi-event``
   node using that path is deployed in a flow. Build the flow first (next
   section), then enable forwarding.

Building a flow
---------------

Open the Node-RED editor (default ``http://NODE-RED-HOST:1880/``). The
**MultiFlexi** palette category contains the four nodes described below.

Create the connection
~~~~~~~~~~~~~~~~~~~~~~~

Add any MultiFlexi node, open it, and create a new **multiflexi-config**:

- **API Base URL** — the full REST base including the version path, e.g.
  ``http://multiflexi.example.com/api/VitexSoftware/MultiFlexi/1.0.0``.
- **Username** / **Password** — MultiFlexi credentials (sent as HTTP Basic auth).

The same config node is reused by every ``multiflexi-runtemplate`` node.

Pattern 1 — event to action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Goal: when a payment-received webhook arrives, send the payment confirmation.

1. Drag a **multiflexi-event** node onto the canvas.

   - **HTTP Path**: ``/multiflexi-event``
   - **Event Type**: ``Webhook change``
   - **Evidence**: ``banka`` (leave blank to match any)
   - **Operation**: ``create``
   - **Token**: the same value as ``NODERED_TOKEN`` (optional)

2. Drag a **multiflexi-runtemplate** node and wire the event node to it.

   - **Server**: the config node created above
   - **RunTemplate ID**: the ID of the *Payment Receipt Confirmation* RunTemplate
   - **Env overrides** (optional): map event fields into job configuration, for
     example ``DOCID`` ← a value carried in ``msg.payload``.

3. (Optional) add a **debug** node after the runtemplate node to inspect the
   scheduling result.
4. Click **Deploy**, then enable ``NODERED_WEBHOOK_URL`` on the daemon as shown
   above.

When a matching change is cached, the daemon POSTs it to ``/multiflexi-event``,
the event node emits it, and the runtemplate node schedules the job.

Pattern 2 — output chaining
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Goal: when a RunTemplate produces a JSON artifact, feed it to a consumer
RunTemplate.

1. Add a **multiflexi-event** node with **Event Type** ``Job completed``.
2. Wire it to a **multiflexi-artifact** node.

   - **Producer RT**: the producing RunTemplate ID (blank = any)
   - **Filename**: ``\.json$`` (regex; blank = any artifact)

3. Wire the artifact node to a **multiflexi-runtemplate** node configured with
   the consumer RunTemplate ID.
4. **Deploy**.

The daemon forwards every finished job as a ``job.completed`` event; the artifact
node emits one message per matching artifact, each launching the consumer
RunTemplate.

Example flow
~~~~~~~~~~~~~

A ready-made flow combining both patterns ships at
``nodered/examples/payment-confirmation.flow.json``. Import it via
**Menu → Import**, set the config node's base URL and credentials, and fill in
your RunTemplate IDs.

Node reference
--------------

multiflexi-config
~~~~~~~~~~~~~~~~~~

Configuration node holding the MultiFlexi REST API connection. Reused by
``multiflexi-runtemplate`` nodes.

- **API Base URL** — full base including the version path.
- **Username** / **Password** — stored encrypted in Node-RED credentials, sent
  as HTTP Basic auth.

multiflexi-event
~~~~~~~~~~~~~~~~~

Input/trigger node. Registers an HTTP ``POST`` route and emits a message for
each event that passes its filters.

*Properties*

- **HTTP Path** — route to register (default ``/multiflexi-event``).
- **Event Type** — ``any``, ``webhook.change`` or ``job.completed``.
- **Evidence** — entity type filter (blank = any).
- **Operation** — ``any``, ``create``, ``update`` or ``delete``.
- **App UUID** — restrict to one application (blank = any).
- **Token** — optional ``X-MultiFlexi-Token`` value; mismatches are rejected with
  HTTP 401. Stored encrypted in credentials.

*Output*

- ``msg.payload`` — the full event JSON.
- ``msg.event`` — the event type string.

multiflexi-runtemplate
~~~~~~~~~~~~~~~~~~~~~~~~

Action node. On each input message it schedules a job for the configured
RunTemplate via ``POST /job/``.

*Properties*

- **Server** — the ``multiflexi-config`` connection.
- **RunTemplate ID** — default RunTemplate to schedule.
- **Executor** — overrides the RunTemplate executor (blank = RunTemplate default).
- **Scheduled** — ``now`` or a ``Y-m-d H:i:s`` timestamp.
- **Env overrides** — static ``KEY``/``value`` pairs injected into the job.

*Input*

- ``msg.runtemplate_id`` — overrides the configured RunTemplate ID.
- ``msg.payload.env`` — environment overrides merged over the static ones (these
  win).
- ``msg.scheduled`` — overrides the scheduled time.

*Output*

- ``msg.payload`` — the API response
  ``{ job_id, runtemplate_id, scheduled, executor, schedule_type }``.

multiflexi-artifact
~~~~~~~~~~~~~~~~~~~~~

Filter node. Splits a ``job.completed`` event into one message per produced
artifact — the output side of a processing chain.

*Properties*

- **Producer RT** — limit to artifacts from a specific producing RunTemplate.
- **Filename** — optional regular expression matched against the filename.

*Output (per artifact)*

- ``msg.payload`` — the artifact descriptor
  ``{ id, filename, content_type, note, created_at }``.
- ``msg.job_id`` / ``msg.runtemplate_id`` / ``msg.app_uuid`` — context copied from
  the originating job event.

Event payloads
--------------

**webhook.change**

.. code-block:: json

   {
     "event": "webhook.change",
     "ts": "2026-06-08T10:30:00+02:00",
     "source_id": 1,
     "source_name": "AbraFlexi demo",
     "adapter_type": "abraflexi-webhook",
     "inversion": 12345,
     "evidence": "banka",
     "operation": "create",
     "recordid": 42,
     "externalids": ""
   }

**job.completed**

.. code-block:: json

   {
     "event": "job.completed",
     "ts": "2026-06-08T10:31:00+02:00",
     "job_id": 987,
     "runtemplate_id": 15,
     "app_id": 10,
     "app_uuid": "c2feac3d-1351-48d3-a019-ecd0b102ef87",
     "company_id": 5,
     "exitcode": 0,
     "schedule_type": "event",
     "executor": "Native",
     "begin": "2026-06-08 10:30:55",
     "end": "2026-06-08 10:31:00",
     "artifacts": [
       { "id": 1, "filename": "result.json", "content_type": "application/json", "note": "Output" }
     ]
   }

REST trigger
------------

The ``multiflexi-runtemplate`` node calls the MultiFlexi REST API. You can issue
the same request manually to test connectivity:

.. code-block:: bash

   curl -u user:pass -X POST \
     http://HOST/api/VitexSoftware/MultiFlexi/1.0.0/job/ \
     -H 'Content-Type: application/json' \
     -d '{"runtemplate_id": 15, "scheduled": "now", "env": {"DOCID": "FV-2025-0042"}}'

The endpoint loads the RunTemplate, validates that it is active, applies the
``env`` overrides, and schedules a job — mirroring
``multiflexi-cli run-template:schedule``. A successful call returns ``201`` with
the new ``job_id``.

Declaring events in app definitions
-----------------------------------

App definition files (``*.app.json``) may declare the business events they emit
or consume via the optional ``events`` block (schema ``3.4.0`` or later).
Orchestrators
use these to suggest connections between producing and consuming applications.

.. code-block:: json

   "events": {
     "emits": {
       "bank.statement.downloaded": {
         "description": { "en": "A bank statement file was downloaded" }
       }
     },
     "consumes": {
       "payment.received": {
         "description": { "en": "A payment was received; send the confirmation" },
         "format": "json"
       }
     }
   }

See :doc:`/reference/application-schema` for the full schema.

Working with the AbraFlexi webhook node
---------------------------------------

The companion ``node-red-contrib-abraflexi`` package provides an
``abraflexi-webhook`` node that receives AbraFlexi Changes-API webhooks directly
into Node-RED (emitting one message per change record). It complements this
integration: wire an ``abraflexi-webhook`` node straight into a
``multiflexi-runtemplate`` node to trigger a RunTemplate from a raw AbraFlexi
change without involving the eventor daemon.

Security
--------

- **Token** — set ``NODERED_TOKEN`` on the daemon and the matching **Token** on
  the ``multiflexi-event`` node so the endpoint rejects unauthenticated POSTs
  (HTTP 401). Secrets are stored encrypted in Node-RED credentials.
- **Transport** — terminate the Node-RED HTTP endpoint behind TLS (reverse proxy)
  when the daemon and Node-RED are on different hosts.
- **API credentials** — the ``multiflexi-config`` node uses HTTP Basic auth;
  prefer a dedicated MultiFlexi API user with the minimum required rights.
- **Editor access** — if Node-RED ``adminAuth`` is enabled, flow changes require
  an editor login; the runtime HTTP route is independent of editor auth.

Verifying and troubleshooting
-----------------------------

**Nodes do not appear in the palette.** Confirm registration and restart:

.. code-block:: bash

   grep -A2 node-red-contrib-multiflexi ~/.node-red/.config.nodes.json
   sudo journalctl -u node-red --since '-5 min' | grep -iE 'multiflexi|error'

**Events are not arriving.** Verify the daemon forwards them and the route exists:

.. code-block:: bash

   # Daemon side — confirm forwarding is configured and the daemon is running
   sudo systemctl status multiflexi-eventor
   sudo journalctl -u multiflexi-eventor --since '-5 min' | grep -i node-red

   # Node-RED side — POST a test event to the deployed route
   curl -s -o /dev/null -w '%{http_code}\n' -X POST \
     http://NODE-RED-HOST:1880/multiflexi-event \
     -H 'Content-Type: application/json' \
     -H 'X-MultiFlexi-Token: change-me' \
     -d '{"event":"webhook.change","evidence":"banka","operation":"create","recordid":1}'

A ``200`` response confirms the ``multiflexi-event`` node is deployed and the
token matches; a ``401`` means the token is wrong; ``404`` means no event node is
deployed on that path.

**Jobs are not scheduled.** Test the REST trigger directly with the ``curl``
command in `REST trigger`_. A ``409`` means the RunTemplate is not active; a
``404`` means the RunTemplate ID does not exist.

**Finished-job events repeat or are missing after a restart.** The daemon tracks
the last forwarded job id in ``NODERED_JOB_STATE_FILE``. Remove that file to
re-initialise from the current maximum job id (only jobs finishing afterwards are
forwarded).
