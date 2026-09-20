Node-RED as MultiFlexi flow editor
==================================

MultiFlexi uses **Node-RED as a visual editor** for automation diagrams.
**multiflexi-eventor** stores and **executes** those diagrams. Node-RED does
not need to be running for chained jobs to continue.

Architecture
------------

1. You draw a flow in Node-RED (event → RunTemplate → map → switch → …).
2. On **Deploy**, ``node-red-contrib-multiflexi`` syncs the Multiflexi subgraph
   to ``POST /api/.../flow/``.
3. MultiFlexi stores an immutable ``flow_version`` (nodes + wires + ports).
4. Eventor starts a ``flow_run`` when a ``multiflexi-event`` trigger matches
   (for example AbraFlexi ``banka/create`` via the webhook acceptor).
5. ``FlowInterpreter`` advances steps: schedule jobs, wait for completion,
   apply ``env_mapping``, branch on ``switch``, honour ``delay``.

Legacy pairwise ``event_rule`` A→B chaining still works beside flows.

Executable node catalog
-----------------------

Only these node types are stored and executed (capability ``1.0.0``):

* ``multiflexi-event``, ``multiflexi-runtemplate``, ``multiflexi-map``,
  ``multiflexi-artifact``, stamp nodes (company / application / credential)
* ``switch``, ``delay``, ``link in``, ``link out``, ``catch``

Other Node-RED palette nodes are ignored or rejected on Deploy so the graph
cannot silently fail at runtime. Arbitrary ``function`` / ``http request``
nodes are out of scope for the PHP interpreter.

Design-only RunTemplate nodes
-----------------------------

``multiflexi-runtemplate`` defaults to **Design only**: it does not call
``POST /job/``. Uncheck Design only only for ad-hoc Inject → schedule from
Node-RED.

API
---

======= ===========================================
Method  Path
======= ===========================================
POST    ``/flow/`` — upsert from Deploy (new version)
GET     ``/flows.{suffix}`` — list flows
GET     ``/flow/{flowId}.{suffix}`` — flow + nodes/wires
GET     ``/flow/{flowId}/runs.{suffix}`` — run history
POST    ``/flow-run/{flowRunId}/cancel.{suffix}``
======= ===========================================

Manual sync from the editor: ``POST /multiflexi/flow/sync`` (Node-RED admin).

Forward-compatible schema
-------------------------

* Immutable ``flow_version``; each ``flow_run`` pins a version.
* Step I/O envelope: ``{payload, env, produced, meta}``.
* Wires carry ``from_port`` / ``to_port``.
* Idempotency key on ``flow_run`` (for example ``change:{source}:{inversion}:…``).
* Job provenance: ``source_job_id``, ``flow_run_id``, ``flow_step_id``.

Node-RED 5
----------

Upgrading Node-RED (including 5.x / Node.js 22+) is an **editor package**
concern. Live ``flow_run`` rows keep executing in eventor on the pinned
``flow_version``.

See also
--------

* :doc:`node-red-authentication`
* Design note: ``passing_data_between_jobs.md`` (workspace root)
