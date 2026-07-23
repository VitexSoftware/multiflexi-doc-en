.. _test-scenarios:

Test Scenarios
==============

This page is the canonical catalogue of **acceptance test scenarios** for
MultiFlexi. Each scenario states the steps a human tester performs, the
reaction the system **must** produce for the scenario to be considered
passing (the "spec"), and — for each of the three surfaces MultiFlexi
exposes (web UI, CLI, REST API) — the best automated technology to verify it
without a human in the loop.

Use this page when:

- deciding whether a feature is "done" (it must satisfy its scenario here,
  not just compile/pass unit tests),
- writing a regression test, so new automation lands next to the scenario it
  proves rather than as an orphaned script,
- triaging a bug report — find the scenario it violates and re-run its
  verification commands.

How to read each scenario
--------------------------

Every scenario has four parts:

- **Goal** — the one-sentence business reason the scenario exists.
- **Steps and expected reaction** — the numbered spec. Each step is
  ``action → expected result``; a scenario only passes if *every* step's
  expected result holds.
- **Verification** — three sub-sections, one per surface:

  - **CLI** — a copy-pasteable sequence of ``multiflexi-cli`` calls (see
    :doc:`/reference/cli`). Suitable for a shell smoke-test script, in the
    style of ``multiflexi-cli/tests/test-cli.sh``.
  - **Web UI (Selenium)** — the automated equivalent in the
    ``multiflexi-web5`` Selenium suite (``tests/selenium/`` inside the
    ``multiflexi-web5`` repository — see :doc:`/selenium-testing`). Where no
    automated test exists yet, the entry is marked **TODO** rather than
    invented.
  - **API (integration test)** — ``curl`` calls against the endpoints in
    :doc:`/reference/api`, plus the matching PHPUnit integration test class
    under ``multiflexi-server/tests/Integration/`` (pattern:
    ``ApiIntegrationTestCase`` subclasses such as
    ``AppApiIntegrationTest.php``, ``RuntemplateApiIntegrationTest.php``,
    ``UserRoleApiIntegrationTest.php``).

A scenario is **functional / accepted** only once at least one of its three
verification paths runs green in CI (or, until automated, has been walked
manually and every expected result confirmed).

.. contents::
   :local:
   :depth: 1

Scenario 1: First system startup
---------------------------------

**Goal:** a freshly installed MultiFlexi reaches a usable, admin-accessible
state.

**Steps and expected reaction:**

1. Run database migrations against an empty schema → migrations complete
   without error; ``multiflexi-cli status`` reports the schema as current.
2. Create the first admin user → user is created and can authenticate.
3. Log in via the web UI with the admin account → dashboard loads, shows
   zero companies/jobs (empty-state, not an error).
4. Log in via the API (``/login/``) with the same account → a token is
   returned.

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli status
    multiflexi-cli status --format=json
    multiflexi-cli user:create --login="admin" --firstname="Admin" \
        --lastname="User" --email="admin@example.com" --plaintext="ChangeMe123!"
    multiflexi-cli user:get --login=admin --format=json

**Verification — Web UI (Selenium)**

``tests/selenium/tests/smoke-test.test.js`` (``npm run test:smoke``) in
``multiflexi-web5`` already covers login + empty-dashboard rendering.
``tests/selenium/tests/simple-smoke.test.js`` (``npm run dev:simple``) covers
the no-database frontend smoke check.

**Verification — API (integration test)**

.. code-block:: bash

    curl -X POST -u admin:ChangeMe123! https://your-server/api/v1/login.json
    curl https://your-server/api/v1/status

PHPUnit: extend ``ApiIntegrationTestCase`` with a ``LoginApiIntegrationTest``
asserting ``/login.json`` returns a token and ``/status`` reports the schema
version (this class does not exist yet — **TODO**, follow the pattern in
``UserRoleApiIntegrationTest.php``).

Scenario 2: User management
-----------------------------

**Goal:** an admin can create, update, and deactivate other users, and the
target user can authenticate and change their own password.

**Steps and expected reaction:**

1. Admin creates a new user with ``enabled=true`` → user appears in
   ``user:list`` / ``GET /users.json``.
2. New user logs in → succeeds, token/session issued.
3. New user's password is changed (self-service or by admin) → old password
   no longer authenticates, new one does.
4. Admin sets ``enabled=false`` → subsequent login attempts by that user are
   rejected (401/403), regardless of correct password.
5. Admin re-enables the account → login succeeds again.

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli user:create --login="jsmith" --firstname="John" --lastname="Smith" \
        --email="jsmith@example.com" --plaintext="secret1" --enabled=true
    multiflexi-cli user:get --login=jsmith --format=json
    multiflexi-cli user:update --login=jsmith --plaintext="secret2"
    multiflexi-cli user:update --login=jsmith --enabled=false
    multiflexi-cli user:update --login=jsmith --enabled=true
    multiflexi-cli user:delete --login=jsmith

**Verification — Web UI (Selenium)**

``tests/selenium/tests/auth.test.js`` (``npm run test:auth``) in
``multiflexi-web5`` covers login/registration. The deactivate/reactivate
admin flow (step 4/5) is **not yet covered** — TODO: extend
``auth.test.js`` or add a dedicated ``user-management.test.js`` using the
existing ``AuthPage.js`` page object.

**Verification — API (integration test)**

.. code-block:: bash

    curl -X POST -u admin:pass -d '{"login":"jsmith","email":"jsmith@example.com","enabled":true}' \
        https://your-server/api/v1/user/
    curl -u jsmith:secret1 https://your-server/api/v1/login.json
    curl -X POST -u admin:pass -d '{"login":"jsmith","enabled":false}' \
        https://your-server/api/v1/user/
    curl -u jsmith:secret1 https://your-server/api/v1/login.json   # must now fail

``UserRoleApiIntegrationTest.php`` already exercises role assignment via
``/user/{id}/roles/``; extend it (or add a sibling
``UserApiIntegrationTest.php``) for the enable/disable-then-login assertion.

Scenario 3: Company onboarding with AbraFlexi
------------------------------------------------

**Goal:** a full company-to-first-successful-job path works end to end for
the most common real-world use case (AbraFlexi accounting integration).

**Steps and expected reaction:**

1. Create a company → appears in ``company:list`` / ``GET /companies.json``.
2. Create/select an ``AbraFlexi`` credential type and a credential instance
   with valid URL/login/password → credential is stored (secret fields
   masked by default, see :doc:`/concepts/credential-management`).
3. Assign an application to the company (``company-app:assign``) → appears
   in ``company-app:list`` for that company.
4. Create a RunTemplate for that company+app and assign the credential to it
   → ``run-template:list-credentials`` shows the assignment.
5. Trigger connectivity/health check for the credential (if the credential
   type implements one) → reports reachable/available.
6. Run the RunTemplate once → job completes with exit code 0 and produces
   the expected output/artifact.

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli company:create --name="Acme Corp" --customer="CustomerX"
    multiflexi-cli company:get --id=1 --format=json
    multiflexi-cli credential-type:list
    multiflexi-cli company-app:assign --company_id=1 --app_id=2
    multiflexi-cli run-template:create --name="Import Invoices" --app_id=2 --company_id=1
    multiflexi-cli run-template:assign-credential --id=1 --credential_id=1
    multiflexi-cli run-template:list-credentials --id=1 --format=json
    multiflexi-cli run-template:schedule --id=1 --executor=Native
    multiflexi-cli job:list --runtemplate_id=1 --order=D --limit=1 --format=json
    multiflexi-cli job:status --id=<job_id_from_above>

**Verification — Web UI (Selenium)**

``tests/selenium/tests/scenario-abraflexi-workflow.test.js``
(``npm run test:abraflexi``) in ``multiflexi-web5`` is the direct equivalent
of this whole scenario (see the "AbraFlexi Complete Workflow" entry in
:doc:`/selenium-testing` and ``TEST-SCENARIOS.md`` "Scenario 3" /
"Scenario 4" in that repo). Supporting page-level tests:
``companies.test.js``, ``credentials.test.js``, ``runtemplate.test.js``.

**Verification — API (integration test)**

.. code-block:: bash

    curl -X POST -u admin:pass -d '{"name":"Acme Corp","customer":"CustomerX"}' \
        https://your-server/api/v1/company/
    curl -X POST -u admin:pass -d '{"name":"Import Invoices","app_id":2,"company_id":1}' \
        https://your-server/api/v1/runtemplate/
    curl -u admin:pass https://your-server/api/v1/runtemplate/1.json

``RuntemplateApiIntegrationTest.php`` and ``AppApiIntegrationTest.php`` cover
the RunTemplate/App CRUD parts today; the credential-assignment +
"run once and observe job success" chain is **TODO** — add a
``CompanyOnboardingApiIntegrationTest.php`` that composes company → credential
→ runtemplate → job creation calls end to end.

Scenario 4: Complete job lifecycle
-------------------------------------

**Goal:** a job goes from scheduled to completed with correct status and
observable output at every transition.

**Steps and expected reaction:**

1. Schedule a job for "now" → job appears with ``status=pending`` /
   ``running``.
2. Job executes → ``job:status`` transitions to a terminal state
   (``success`` or ``failed``) with a non-null ``exitcode``.
3. Retrieve job output/log → stdout/stderr and any produced artifact are
   available and non-empty for a successful run of an app that produces
   output.
4. If the RunTemplate has a recurring interval, its ``next_schedule`` /
   ``last_schedule`` is updated only for interval-triggered jobs, not for
   ad-hoc ones (see ``schedule_type`` semantics in :doc:`/reference/cli`).

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli job:create --runtemplate_id=1 --scheduled="now"
    multiflexi-cli job:status --id=<job_id>
    multiflexi-cli job:get --id=<job_id> --format=json
    multiflexi-cli job:list --status=success --runtemplate_id=1 --format=json
    multiflexi-cli job:list --status=failed --runtemplate_id=1 --format=json

**Verification — Web UI (Selenium)**

``tests/selenium/tests/jobs.test.js`` (``npm run test:jobs``) covers job
listing/detail rendering in ``multiflexi-web5``.
``scenario-abraflexi-workflow.test.js`` covers the manual-trigger-then-observe
flow. A dedicated "watch a running job update live" test is **TODO** (ties
into "Scenario 12: Real-time monitoring" in that repo's ``TEST-SCENARIOS.md``,
not yet implemented).

**Verification — API (integration test)**

.. code-block:: bash

    curl -X POST -u admin:pass -d '{"runtemplate_id":1,"scheduled":"now"}' \
        https://your-server/api/v1/job/
    curl -u admin:pass https://your-server/api/v1/job/<id>.json

Add a ``JobLifecycleApiIntegrationTest.php`` (pattern per
``RuntemplateApiIntegrationTest.php``) asserting the job transitions from
pending to a terminal status within a bounded poll timeout — **TODO**, no
such test exists yet.

Scenario 5: Error handling and task recovery
------------------------------------------------

**Goal:** failures are reported accurately and, where a retry budget exists
(see :doc:`/concepts/tasks`), the Task layer retries within its window
instead of silently giving up.

**Steps and expected reaction:**

1. Run a job against a RunTemplate with invalid/expired credentials → job
   ends ``failed`` with a diagnosable error message (not a silent success).
2. Run a job referencing a deleted/non-existent application → CLI/API
   rejects the operation with a clear error, no job is created.
3. For a RunTemplate configured with ``--max_attempts`` > 1, a first failed
   attempt within the task window schedules a retry automatically; the Task
   stays ``open``/``running`` until either a later attempt succeeds
   (→ ``fulfilled`` or ``fulfilled_late`` depending on ``--deadline_offset``)
   or attempts/window are exhausted (→ ``failed``/``missed``).

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli run-template:create --name="Flaky Import" --app_id=2 --company_id=1 \
        --max_attempts=3 --retry_backoff=fixed --retry_min_gap=60 --allow_late=false
    multiflexi-cli run-template:schedule --id=<id>
    multiflexi-cli task:list --runtemplate_id=<id> --format=json
    multiflexi-cli task:get --id=<task_id> --with-jobs --format=json
    multiflexi-cli job:list --runtemplate_id=999999   # nonexistent -> expect clean error, no job

**Verification — Web UI (Selenium)**

``tests/selenium/tests/scenario-error-recovery.test.js``
(``npm run test:errors``) in ``multiflexi-web5`` already exercises invalid
credentials / nonexistent app / timeout flows ("Job Error Recovery" business
scenario, see :doc:`/selenium-testing`). The Task-level retry-then-fulfil
view is **TODO** — the web UI's task/monitoring page did not exist when that
suite was written.

**Verification — API (integration test)**

.. code-block:: bash

    curl -u admin:pass https://your-server/api/v1/tasks.json?state=failed
    curl -u admin:pass https://your-server/api/v1/task/<id>.json

Add a ``TaskApiIntegrationTest.php`` — **TODO**, no integration test covers
``/task/`` or ``/tasks.json`` yet; follow the ``RuntemplateApiIntegrationTest.php``
pattern.

Scenario 6: Credential management and encryption
-----------------------------------------------------

**Goal:** stored credentials are never exposed in normal reads, encryption
keys can be rotated without breaking existing credentials, and revealing a
secret is audited.

**Steps and expected reaction:**

1. Create a credential with a secret field → ``credential:get`` shows the
   value masked (``••••••••``) by default.
2. ``credential:get --reveal`` prompts for interactive confirmation and, once
   confirmed, shows the real value, and writes an audit log entry.
3. The REST API and web UI **never** expose the raw secret value (only the
   CLI ``--reveal`` path can) — see :doc:`/concepts/credential-management`.
4. ``encryption:init --force`` rotates the active key version → previously
   encrypted credentials still decrypt correctly (old version stays
   inactive-but-usable); ``encryption:status`` shows the new version active.

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli credential:get --id=1
    multiflexi-cli credential:get --id=1 --reveal
    multiflexi-cli encryption:status --format=json
    multiflexi-cli encryption:init --force
    multiflexi-cli encryption:status --format=json
    multiflexi-cli credential:get --id=1 --reveal   # must still decrypt correctly after rotation

**Verification — Web UI (Selenium)**

``tests/selenium/tests/credentials.test.js`` (``npm run test:credentials``)
in ``multiflexi-web5`` covers create/list/mask rendering. Confirming the web
UI *never* offers a reveal control is a negative assertion **TODO** to add
explicitly (assert the reveal control/element does not exist in the DOM).
Key rotation has no UI surface — CLI/API only, so no Selenium coverage is
expected here.

**Verification — API (integration test)**

.. code-block:: bash

    curl -u admin:pass https://your-server/api/v1/credential/1.json   # must be masked, no raw secret

Add a ``CredentialApiIntegrationTest.php`` asserting the response never
contains an unmasked secret field — **TODO**, this is a security-relevant
gap in current integration coverage and should be prioritized.

Scenario 7: Application assignment to a company
----------------------------------------------------

**Goal:** applications can be attached to / detached from a company
independently of any RunTemplate, and the assignment is queryable.

**Steps and expected reaction:**

1. Assign an application to a company → appears in
   ``company-app:list --company_id=<id>``.
2. Filtering by both ``company_id`` and ``app_id`` returns exactly that pair
   (or ``app_uuid`` resolves to the same ``app_id``).
3. Unassign → the pair no longer appears in the list.

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli company-app:assign --company_id=1 --app_id=2
    multiflexi-cli company-app:list --company_id=1 --app_id=2 --format=json
    multiflexi-cli company-app:assign --company_id=1 --app_uuid="uuid-123" --format=json
    multiflexi-cli company-app:unassign --company_id=1 --app_id=2
    multiflexi-cli company-app:list --company_id=1 --app_id=2 --format=json   # must now be empty

**Verification — Web UI (Selenium)**

``tests/selenium/tests/applications.test.js`` (``npm run test:applications``)
and ``companies.test.js`` in ``multiflexi-web5`` cover the individual pages;
an explicit assign/unassign round-trip scenario is **TODO**.

**Verification — API (integration test)**

.. code-block:: bash

    curl -u admin:pass https://your-server/api/v1/company/1/users.json   # roster example pattern to follow

No dedicated ``company-app`` REST endpoint is documented in
:doc:`/reference/api` today — the CLI's ``company-app:*`` commands operate
directly on RunTemplate rows. Treat the CLI path above as authoritative
until/unless a REST endpoint is added; **TODO** flag for whoever adds one to
also add its integration test.

Scenario 8: Event rule chaining (job A completion triggers job B)
-----------------------------------------------------------------------

**Goal:** an EventRule correctly maps a source event to a triggered
RunTemplate, per the passing-data-between-jobs design
(see ``passing_data_between_jobs.md``).

**Steps and expected reaction:**

1. Create an EventSource → ``event-source:test`` reports the adapter
   database reachable.
2. Create an EventRule bound to that source with an ``env_mapping`` and a
   target ``runtemplate_id`` → rule appears in ``event-rule:list``.
3. A matching event on the source triggers a job for the target RunTemplate,
   with the mapped environment overrides applied (visible in the triggered
   job's environment, not the RunTemplate's saved config).

**Verification — CLI**

.. code-block:: bash

    multiflexi-cli event-source:create --name="Accounting DB" --dsn="mysql:host=..." \
        --username=... --password=...
    multiflexi-cli event-source:test --id=1
    multiflexi-cli event-rule:create --event_source_id=1 --evidence="invoice" \
        --operation=create --runtemplate_id=5 --priority=0 --enabled=1 \
        --env_mapping='{"INVOICE_ID":"id"}'
    multiflexi-cli event-rule:list --format=json
    multiflexi-cli event-rule:get --id=1 --format=json

**Verification — Web UI (Selenium)**

No web UI or Selenium coverage exists for event rules yet (**TODO** —
depends on Phase 4 of the passing-data-between-jobs design, the Node-RED
mapping GUI described in ``passing_data_between_jobs.md``; not a
``multiflexi-web5`` gap, the feature's own admin UI is not yet built).

**Verification — API (integration test)**

.. code-block:: bash

    curl -X POST -u admin:pass -d '{"event_source_id":1,"evidence":"invoice","operation":"create","runtemplate_id":5}' \
        https://your-server/api/v1/eventrule/
    curl -u admin:pass https://your-server/api/v1/eventrules.json
    curl -X POST -u admin:pass https://your-server/api/v1/eventsource/1/test.json

Add an ``EventRuleApiIntegrationTest.php`` — **TODO**, no integration test
exists yet.

Scenario 9: REST API authentication
---------------------------------------

**Goal:** the API enforces HTTP Basic Authentication uniformly, with the
documented exceptions.

**Steps and expected reaction:**

1. Request any protected endpoint without credentials → ``401``.
2. Request with valid ``Authorization: Basic`` credentials → ``200`` with
   the expected payload.
3. Request ``/ping``, ``/login``, or the API index root without credentials
   → succeeds (documented exemptions).
4. Credentials embedded in the URL (``user:pass@host``) are rejected/ignored
   — only the header form works.

**Verification — CLI**

Not directly applicable — ``multiflexi-cli`` talks to the database, not the
REST API. Use ``token:*`` commands to manage the API tokens that back this
scenario:

.. code-block:: bash

    multiflexi-cli token:generate --user=1
    multiflexi-cli token:list --format=json

**Verification — Web UI (Selenium)**

Not applicable — this is a backend contract, not a UI flow.

**Verification — API (integration test)**

.. code-block:: bash

    curl -i https://your-server/api/v1/apps.json                        # expect 401
    curl -i -u admin:pass https://your-server/api/v1/apps.json          # expect 200
    curl -i https://your-server/api/v1/ping.json                        # expect 200, no auth
    curl -i https://your-server/api/v1/login.json -u admin:pass         # expect 200 + token

``ApiIntegrationTestCase.php`` already provides the authenticated-client
scaffolding used by every other integration test in this catalogue; add an
``AuthApiIntegrationTest.php`` asserting the 401/exemption matrix explicitly
— **TODO**, currently only implicitly covered by every other test needing
auth to pass.

Summary: automation coverage by surface
-------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 25 25

   * - Scenario
     - CLI
     - Web UI (Selenium)
     - API (integration test)
   * - 1. First system startup
     - covered
     - covered
     - TODO
   * - 2. User management
     - covered
     - partial (enable/disable TODO)
     - partial (enable/disable TODO)
   * - 3. Company onboarding (AbraFlexi)
     - covered
     - covered
     - partial (chain TODO)
   * - 4. Job lifecycle
     - covered
     - partial (live updates TODO)
     - TODO
   * - 5. Error handling / task recovery
     - covered
     - partial (task view TODO)
     - TODO
   * - 6. Credentials & encryption
     - covered
     - partial (negative assertion TODO)
     - TODO (security-relevant, prioritize)
   * - 7. Application assignment
     - covered
     - partial (round-trip TODO)
     - no REST endpoint yet
   * - 8. Event rule chaining
     - covered
     - not applicable yet (no UI)
     - TODO
   * - 9. API authentication
     - n/a (tokens only)
     - not applicable
     - partial (explicit matrix TODO)

This table is maintained by hand — update it whenever a TODO item above gets
implemented.
