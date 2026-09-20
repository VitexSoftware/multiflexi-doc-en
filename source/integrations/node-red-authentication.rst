Node-RED Authentication and Authorization
===========================================

This page walks through exactly how MultiFlexi and Node-RED authorize their
communication with each other. There are three separate trust relationships
involved, and understanding all three is the fastest way to diagnose a chain
that silently does not fire.

.. contents::
   :local:
   :depth: 1

Overview
--------

.. code-block:: text

    ┌─────────────┐   1. X-MultiFlexi-Token   ┌─────────────┐
    │ MultiFlexi   │ ────────────────────────> │  Node-RED    │
    │ (eventor)    │   webhook / catalog push  │  (receiver)  │
    └─────────────┘                            └─────────────┘

    ┌─────────────┐   2. Authorization: Bearer ┌─────────────┐
    │  Node-RED    │ ────────────────────────> │ MultiFlexi   │
    │ (flow nodes) │   POST /job/, /eventrule/  │   API        │
    └─────────────┘                            └─────────────┘

    ┌─────────────┐   3. login + RBAC role     ┌─────────────┐
    │  A person    │ ────────────────────────> │  Node-RED    │
    │  in a browser│   maps to editor perms    │  admin UI    │
    └─────────────┘                            └─────────────┘

Each direction uses a different credential and serves a different purpose.
None of them are interchangeable.

1. MultiFlexi → Node-RED: the webhook shared secret
------------------------------------------------------

The ``multiflexi-eventor`` daemon pushes two kinds of HTTP POST requests into
Node-RED:

- **Events** (``webhook.change``, ``job.completed``) to the ``multiflexi-event``
  node's route (default ``/multiflexi-event``).
- **Catalog updates** (companies, run-templates, credentials) to the
  ``multiflexi-catalog`` node's route (default ``/multiflexi-catalog``).

Both routes require a shared secret sent as the ``X-MultiFlexi-Token`` header.
The secret is **mandatory** - a ``multiflexi-event`` or ``multiflexi-catalog``
node with no token configured refuses to register its HTTP route at all
(check the Node-RED log for "no X-MultiFlexi-Token shared secret configured"
and the node's status will show "no shared secret - route disabled").

**Setting the secret**

The same value must be configured on both ends:

- On the MultiFlexi side, via debconf when installing/reconfiguring
  ``multiflexi-eventor``:

  .. code-block:: bash

      sudo dpkg-reconfigure multiflexi-eventor
      # prompts for NODERED_TOKEN when a webhook URL is set

- On the Node-RED side, open the ``multiflexi-event`` (and separately the
  ``multiflexi-catalog``) node's editor and paste the same value into its
  **Token** credential field. It is stored encrypted by Node-RED's standard
  credentials mechanism.

**Rotating the secret**: re-run ``dpkg-reconfigure multiflexi-eventor`` with a
new value, then update the token in both the ``multiflexi-event`` and
``multiflexi-catalog`` node editors and redeploy the flow. There is a short
window during rotation where old pushes are rejected with ``401`` - this is
expected and not an error to chase.

The comparison is constant-time (not a plain string ``===``), so a shared
secret compare cannot leak timing information about how much of the token
matched.

2. Node-RED → MultiFlexi: the API bearer token
-------------------------------------------------

On a **MultiFlexi-hosted** Node-RED the connection is implicit. Set these
environment variables on the Node-RED process (Ansible writes them to
``/etc/default/node-red``):

- ``MULTIFLEXI_URL`` — API root, e.g. ``http://127.0.0.1/multiflexi/api``
- ``MULTIFLEXI_API_TOKEN`` — bearer token for a dedicated service account
  (e.g. ``svc-nodered``)

Run-template and map nodes then call ``POST /job/`` and related endpoints
**without** a ``multiflexi-config`` node. The service account becomes
``job.launched_by`` for automated event-driven runs (same idea as the
scheduler's ``UnixUser``).

For **standalone** Node-RED (talking to a remote MultiFlexi), keep using a
``multiflexi-config`` node:

- **API Token** (recommended): ``Authorization: Bearer <token>``.
- **Username/Password** (legacy): HTTP Basic, only when no token is set.

**Minting a token**

Create a dedicated service account (e.g. ``svc-nodered``), give it the roles
it needs (schedule jobs, read catalog, manage ``event_rule``) via MultiFlexi
RBAC, then:

.. code-block:: bash

    multiflexi-cli token:generate --login svc-nodered --ttl "+180 days"

Put the token in ``MULTIFLEXI_API_TOKEN`` (hosted) or the config node's
**API Token** field (standalone).

**Ad-hoc launches from the editor**: tick **Record me as launcher** on a
run-template node. The job then gets ``schedule_type=event`` and
``launched_by`` = your MultiFlexi user id, while the Bearer token remains
the service account.

The **RunTemplate** field in the node editor autosuggests from
``GET /nodered/catalog.json`` (match by numeric id or name). **Executor**
is a drop-down of classes installed on the MultiFlexi host
(``GET /nodered/executors.json`` / ``catalog.executors``); leave it blank
to keep the RunTemplate's own default.

**What happens on the server**: the API checks for a bearer token first. A
valid token logs that user in for the request. A present-but-invalid token
is rejected; no token falls through to Basic auth.

3. A person logging into the Node-RED editor
-------------------------------------------------

Deployments should enable ``multiflexi-auth.js`` as Node-RED's ``adminAuth``
(Ansible default when ``multiflexi_server_nodered_multiflexi_auth`` is true):

- Username/password is checked against MultiFlexi's ``/login`` endpoint.
- The API token from that login is **kept** in the editor session and used to
  call ``GET /nodered/catalog.json``, which returns only companies /
  run-templates / credentials the user may see (``company_user`` + admin
  bypass), plus the host's installed ``executors`` list. Generic node
  editors (RunTemplate / Company) use that list for autosuggest.
- A successful login is **not** granted full Node-RED admin rights by
  default — MultiFlexi users get read-only editor access unless the
  deployment grants broader permissions separately.
- Session TTL is short (5 minutes, sliding on activity).

.. note::

   Mapping MultiFlexi RBAC roles onto Node-RED editor ``*`` permissions is
   still a future enhancement. Until then, read-only is the safe default for
   MultiFlexi-authenticated logins.

Worked example: one chained job, end to end
------------------------------------------------

Run-template **A** downloads a bank statement and produces
``invoices.json``; run-template **B** processes invoices and consumes a file
via ``INPUT_FILE``. A ``multiflexi-map`` binding connects them. Here is
every authorization check that fires when A finishes:

#. Job A finishes. ``multiflexi-eventor`` POSTs a ``job.completed`` event to
   Node-RED's ``multiflexi-catalog``/``multiflexi-event`` routes, presenting
   ``X-MultiFlexi-Token`` — **checkpoint 1**. A wrong or missing token here
   means the event never reaches Node-RED at all (check the Node-RED log for
   a ``401`` warning).
#. Separately (and independently of the Node-RED push), the
   ``JobChainProcessor`` daemon on the MultiFlexi server side notices job A
   finished, finds the ``event_rule`` created by the ``multiflexi-map`` node,
   resolves its ``env_mapping`` against A's produced data, and schedules job
   B via ``multiflexi-cli run-template:schedule`` directly - this internal
   path does not go through the Node-RED API call at all, so it is not
   gated by checkpoint 2 below.
#. If instead you *edited* the binding through the ``multiflexi-map`` node's
   editor (rather than it having been created ahead of time), that editor
   action itself calls ``POST /eventrule/`` on the MultiFlexi API, presenting
   the ``multiflexi-config`` node's bearer token — **checkpoint 2**. A
   missing/expired/wrong-scope token here means the binding never saves, and
   the mapping editor UI shows the API error.
#. Job B runs with ``INPUT_FILE`` pointing at a temp file materialized from
   A's produced JSON, then that temp file is removed once B has read it.

If a chain "silently doesn't fire," check checkpoints 1 and 2 in that order:
first confirm the webhook token is accepted (Node-RED log), then confirm the
``multiflexi-map`` node's own API calls are authenticating (its status/error
output in the flow editor).

See Also
--------

- :doc:`../concepts/job-chaining` - the run-template A → B chaining concept
  and the ``multiflexi-map`` node's mapping UI.
- :doc:`../reference/api` - full API authentication reference (Bearer vs.
  Basic, exempt paths).
- :doc:`../administration/systemd-services` - ``multiflexi-eventor``'s
  ``NODERED_*`` environment variables.
