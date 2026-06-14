.. _topics:

Topics: Credential Providers and Consumers
===========================================

A **Topic** is a named capability contract. It bridges what an application *needs*
and what a credential *provides*, making it possible for MultiFlexi to automatically
match applications with the right credentials at both configuration time and runtime.

The Two Sides of a Topic
-------------------------

**Provider**
  A credential (instantiated from a **CredentialProtoType**) declares that it
  provides one or more topics. For example, a credential based on the ``FioBank``
  prototype provides topic ``FioBank``.

**Consumer**
  An application declares the topics it *requires* in the ``requirements`` section
  of its ``app.json`` definition. A RunTemplate cannot start a job until every
  required topic is satisfied by an assigned credential.

Example — bank statement downloader:

.. code-block:: json

    {
      "requirements": ["FioBank"]
    }

When a RunTemplate is configured, the administrator assigns a ``FioBank`` credential
to satisfy the ``FioBank`` requirement. The UI shows an error if no suitable
credential type is defined for the company, or a warning if no credential is yet
assigned.

Two-Phase Resolution
--------------------

Topic resolution happens in two phases at different points in the job lifecycle.

Phase 1 — Static Binding (Configuration Time)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Does a credential of a type that provides the topic exist, and is it assigned to
the RunTemplate?*

This is a binary check performed in the web UI when the administrator configures a
RunTemplate:

- **Provider not installed** → the requirement card shows red (``danger``). The
  required extension package must be installed.
- **Provider installed, no credential type defined** → the card shows orange
  (``warning``). A credential type must be created for the company first.
- **Credential type exists, no credential assigned** → the card shows a dropdown
  for the administrator to choose or create a credential.
- **Credential assigned** → the card shows green (``success``) and the current
  live availability badge (see Phase 2).

Phase 2 — Dynamic Verification (Job Runtime)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Is the backing service actually reachable and the credential valid right now?*

Immediately before starting a job, the executor calls ``checkAvailability()`` on
every assigned credential's prototype. The result determines whether the job runs:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - State
     - Job outcome
     - Meaning
   * - ``available``
     - Runs
     - Service live, credential valid
   * - ``unknown``
     - Runs
     - No check implemented — backward compatible, never blocks
   * - ``degraded``
     - Deferred
     - Service reachable but impaired (e.g. server busy or under load)
   * - ``unavailable``
     - Deferred
     - Transient failure: timeout, connection refused, 5xx response
   * - ``misconfigured``
     - Blocked (no retry)
     - Permanent fault: bad token, unreadable certificate, missing field

Deferred jobs are re-queued after the check's TTL (seconds) expires.
``misconfigured`` jobs are never retried — administrator action is required.

All non-``available`` / non-``unknown`` results are reported to the SQL log,
Zabbix (when ``ZABBIX_SERVER`` is set), and OpenTelemetry (when ``OTEL_ENABLED``
is set). Blocked jobs appear in the job list with exit code **75** (POSIX
``EX_TEMPFAIL``) and an orange ``job-credential-blocked`` row class.

Relationship Diagram
--------------------

.. code-block:: text

    app.json
    ┌────────────────────────────┐
    │  "requirements": ["FioBank"]│  ← consumer declares needed topic
    └───────────────┬────────────┘
                    │  Phase 1 (config time)
                    ▼
    ┌─────────────────────────────────┐
    │  RunTemplate  ─── Credential    │  ← administrator assigns provider
    │  (assigned at configuration)    │
    └───────────────┬─────────────────┘
                    │  Phase 2 (runtime, per-job)
                    ▼
    ┌──────────────────────────────────────────┐
    │  CredentialProtoType.checkAvailability() │
    │  returns CredentialCheckResult           │
    └──────────┬───────────────────────────────┘
               │
    ┌──────────▼──────────────────────────────────────┐
    │  isSatisfied()?                                  │
    │   true  (available / unknown)  → run job         │
    │   false (degraded / unavailable) → defer + retry │
    │   false (misconfigured)          → block, notify │
    └──────────────────────────────────────────────────┘

Web UI Indicators
-----------------

**RunTemplate configuration page**
  Each requirement card shows a live availability badge after the credential
  dropdown:

  - ✅ ``available`` — green
  - ⚠️ ``degraded`` — orange
  - 🔴 ``unavailable`` — red
  - 🚫 ``misconfigured`` — red
  - ℹ️ ``unknown`` — blue (no check implemented)

**Credential configuration form**
  When no custom UI helper exists for the credential type, the form renders a
  universal availability panel (alert + optional details list) after the field
  inputs. Credential types with a dedicated UI helper (e.g. mServer) render
  their own availability section instead.

**Job list**
  Jobs blocked by a failed credential check appear with exit code ``75`` and an
  orange row background (``job-credential-blocked``).

Implementing a Topic Provider
------------------------------

A credential prototype becomes a topic provider by:

1. Its PHP class name (e.g. ``MultiFlexi\CredentialProtoType\FioBank``) matching
   the topic name (e.g. ``FioBank``) in ``app.json``.
2. Optionally implementing ``checkAvailability()`` for Phase 2 live checks:

.. code-block:: php

    namespace MultiFlexi\CredentialProtoType;

    class FioBank extends \MultiFlexi\CredentialProtoType
        implements \MultiFlexi\credentialTypeInterface,
                   \MultiFlexi\checkableCredentialInterface
    {
        #[\Override]
        public function checkAvailability(): \MultiFlexi\CredentialCheckResult
        {
            $token = (string) ($this->configFieldsInternal
                ->getFieldByCode('FIO_TOKEN')?->getValue() ?? '');

            if ($token === '') {
                return new \MultiFlexi\CredentialCheckResult(
                    \MultiFlexi\CredentialState::Misconfigured,
                    _('FIO_TOKEN is not set'),
                    time(),
                );
            }

            // Host-reachability only — avoids 30 s rate limit and cursor side effect.
            $ch = curl_init('https://fioapi.fio.cz/');
            curl_setopt_array($ch, [\CURLOPT_NOBODY => true, \CURLOPT_CONNECTTIMEOUT => 5, \CURLOPT_TIMEOUT => 5]);
            curl_exec($ch);
            $errno = curl_errno($ch);

            return $errno === 0
                ? new \MultiFlexi\CredentialCheckResult(\MultiFlexi\CredentialState::Available, '', time(), 300)
                : new \MultiFlexi\CredentialCheckResult(\MultiFlexi\CredentialState::Unavailable,
                      sprintf(_('Fio API unreachable: %s'), curl_strerror($errno)), time(), 60);
        }
    }

The base class ``\MultiFlexi\CredentialProtoType`` provides a default no-op
implementation that returns ``Unknown`` — so prototypes without a live check never
block jobs, ensuring backward compatibility.

See Also
--------

- :ref:`credential-management` — three-tier credential architecture
- :doc:`credential-prototype` in the development section — implementing credential prototypes
- :ref:`credential-availability-checks` — check states and built-in implementations
- :doc:`job-lifecycle` — how job states relate to topic satisfaction
