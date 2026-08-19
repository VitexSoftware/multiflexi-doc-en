Audit Logging
=============

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

Every create, update, and delete performed on any MultiFlexi entity — RunTemplate, Company, Credential, User, Job, EventRule, and so on — is recorded automatically to the ``security_audit_log`` table. This happens regardless of whether the action came from the web UI, the CLI (``multiflexi-cli``), or the REST API, because all three surfaces call the same underlying model classes.

This closes a gap that existed before: logging used to be opt-in per call site (via ``addStatusMessage()``), so entities whose code never explicitly logged an action — most notably deletes — left no trace. RunTemplate deletion was one such gap; it is now covered like every other entity.

Where entries come from
------------------------

``MultiFlexi\DBEngine`` — the base class most model classes extend — and ``MultiFlexi\User`` (which uses the ORM trait directly) both override ``insertToSQL()``, ``updateToSQL()``, and ``deleteFromSQL()`` to write one ``security_audit_log`` row after every successful write, via the shared ``MultiFlexi\Security\AuditableEntity`` trait and ``MultiFlexi\Security\AuditLog::record()`` helper.

Because this is a single choke point shared by every model, cascading deletes (for example RunTemplate's cascade across Job, ActionConfig, RunTplCreds, Configuration, and EventRule rows) produce one audit entry per affected row, not just one for the top-level entity.

.. note::

   Logging is best-effort: a failure to write an audit row never blocks or fails the operation being audited.

Recorded fields
----------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Meaning
   * - ``user_id``
     - The acting user; ``null`` for unattended actions (e.g. the scheduler daemon creating a Job with no logged-in session).
   * - ``entity_type``
     - Short class name of the audited entity, e.g. ``RunTemplate``, ``Company``, ``Credential``.
   * - ``entity_id``
     - Primary key of the affected row. May be ``null`` for a multi-row delete whose filter didn't directly name the key column.
   * - ``action``
     - ``create`` | ``update`` | ``delete``.
   * - ``event_description``
     - Human-readable summary, e.g. ``RunTemplate delete #42``.
   * - ``severity``
     - Reused from the pre-existing security-event severity scale (``low``/``medium``/``high``/``critical``); generic entity CRUD entries default to ``low``.
   * - ``additional_data``
     - Extra JSON context — for example the filter conditions used on a multi-row delete.
   * - ``created_at``
     - Timestamp of the action.

``security_audit_log`` predates this feature and already carried authentication/security events (login attempts, 2FA, role changes) via ``event_type``; those columns are untouched. ``entity_type``/``entity_id``/``action`` are additive columns used only by the generic entity-CRUD entries described here.

Viewing audit entries
----------------------

- **Web UI**: the *My Recent Actions* panel on the dashboard (``home.php``) shows the logged-in user's own audit trail — this is what now shows a RunTemplate deletion that the free-text *My Recent Activity Log* panel above it does not capture, since that older panel only shows whatever a call site explicitly chose to log. The *Audit Log* page (``auditlog.php``, linked from the admin menu) shows the full, system-wide trail.
- **REST API**: see :ref:`the /auditlog endpoints <api_endpoints>` in :doc:`../reference/api` — ``GET /auditlog.{suffix}`` (filterable by ``user_id``, ``entity_type``, ``entity_id``, ``action``, ``from``, ``to``) and ``GET /auditlog/{auditLogId}.{suffix}``.

Known limitation
-----------------

``MultiFlexi\User`` is audited separately from ``DBEngine``-based models because it uses the ``Ease\SQL\Orm`` trait directly rather than extending ``DBEngine``. Both paths write through the same ``AuditableEntity`` trait, so coverage is equivalent — this is only a code-organization detail, not a gap.
