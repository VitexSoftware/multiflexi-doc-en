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

Every node that calls the MultiFlexi REST API - ``multiflexi-runtemplate``
(``POST /job/``) and ``multiflexi-map`` (``GET``/``POST``/``PUT
/eventrule/``, catalog reads) - authenticates through a ``multiflexi-config``
node. That config node now supports two credential modes:

- **API Token** (recommended): a bearer token, sent as
  ``Authorization: Bearer <token>``.
- **Username/Password** (legacy): HTTP Basic auth with a real MultiFlexi user
  account, used only when no token is configured.

Prefer the token. It means Node-RED never has to hold a human user's
password, and the token can be scoped to a dedicated low-privilege service
account instead of an admin login.

**Minting a token**

Create a dedicated service account per environment (e.g. ``svc-nodered``) if
one does not already exist, give it only the roles it actually needs
(schedule jobs, read the app/run-template catalog, manage ``event_rule``
bindings) via MultiFlexi's RBAC, then issue a token for it:

.. code-block:: bash

    multiflexi-cli token:generate --login svc-nodered --ttl "+180 days"
    # Token issued for user #7 (save it now, it will not be shown again):
    # 8f3c1a9e2b7d4f6081ac...
    # Expires: 2027-02-25 00:00:00

The token is shown exactly once - copy it straight into the
``multiflexi-config`` node's **API Token** field in the Node-RED editor.
Omit ``--ttl`` for a token that never expires (only do this for a
well-monitored service account).

**What happens on the server**: the API checks for a bearer token first. A
valid, unexpired token belonging to an enabled user logs that user in for the
request (equivalent to a successful Basic-auth login), so every downstream
permission check behaves exactly as it would for that user logging in
interactively. A present-but-invalid or expired token is rejected outright -
it does not silently fall back to Basic auth. No token on the request at all
falls through to Basic auth unchanged, so existing username/password
``multiflexi-config`` nodes keep working.

**Revoking access**: disabling the service account (or deleting its token
row) immediately invalidates every request using that token - there is no
separate revocation list to maintain.

3. A person logging into the Node-RED editor
-------------------------------------------------

Where the deployment enables `multiflexi-auth.js` as Node-RED's
``adminAuth`` (see the ``multiflexi_server`` Ansible role's
``nodered.yml``), a person's Node-RED editor login is itself validated
against MultiFlexi:

- The username/password they type is checked against MultiFlexi's real
  ``/login`` endpoint (the same password check the API itself uses).
- A successful login is **not** granted full Node-RED admin rights by
  default - every MultiFlexi user who authenticates this way gets read-only
  editor access. The single account configured with full edit rights is the
  one set up by the deployment (``multiflexi_server_nodered_admin_user`` /
  ``_admin_password_hash`` in the Ansible role), independent of this dynamic
  MultiFlexi-backed login path.
- A login session is remembered for a short time (5 minutes) before it must
  be re-validated; nothing is ever granted to a username that has not just
  authenticated successfully.

.. note::

   Mapping specific MultiFlexi RBAC roles onto Node-RED editor permissions
   (so, for example, a MultiFlexi admin automatically gets Node-RED edit
   rights too) needs a REST endpoint exposing a user's roles, which does not
   exist yet. Until then, read-only is the deliberate safe default for every
   MultiFlexi-authenticated login.

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
