HouseKeeper — Periodic Maintenance
====================================

**Target Audience:** Administrators
**Difficulty:** Beginner
**Prerequisites:** MultiFlexi running; ``multiflexi-housekeeper`` installed

.. contents::
   :local:
   :depth: 2

Overview
--------

``multiflexi-housekeeper`` is a periodic maintenance daemon that keeps the MultiFlexi
platform healthy and prevents data accumulation problems. It runs once per hour via a
**systemd timer** and executes eight housekeeping duties in a defined order.

Install
-------

.. code-block:: bash

   sudo apt install multiflexi-housekeeper

The package automatically enables and starts the ``multiflexi-housekeeper.timer``
systemd unit. No further configuration is required for a default deployment.

How It Works
------------

The HouseKeeper is intentionally **not** a continuously-running daemon like the
scheduler or executor. Instead it uses a systemd ``Type=oneshot`` service triggered
by a ``OnCalendar=hourly`` timer with up to 5 minutes of random jitter
(``RandomizedDelaySec=300``).

The ``Persistent=true`` timer option ensures that if the system was offline when a
scheduled run was due, the run executes on the next boot — no maintenance window is
silently skipped.

.. code-block:: bash

   # Check when the next run is scheduled
   systemctl list-timers multiflexi-housekeeper

   # Trigger an immediate run without waiting for the timer
   sudo systemctl start multiflexi-housekeeper.service

   # Preview what would be done without making changes
   sudo -u multiflexi multiflexi-housekeeper --dry-run

Duties
------

The eight duties run in the order shown. Each duty catches its own exceptions so a
failure in one duty does not abort the rest.

.. list-table::
   :header-rows: 1
   :widths: 5 25 70

   * - #
     - Duty
     - What it does
   * - 1
     - **StaleTaskFinalization**
     - Marks ``open`` or ``running`` Tasks whose ``window_end`` has passed.
       Tasks with zero attempts become ``missed``; tasks with at least one
       attempt become ``failed``. Provides a safety net for when the scheduler
       daemon is temporarily offline and cannot finalize tasks itself.
   * - 2
     - **OrphanedJobCleanup**
     - Removes jobs that reference deleted companies or RunTemplates, schedule
       queue entries that point to non-existent jobs, and "ghost" jobs that were
       never started and have no queue entry for longer than
       ``MULTIFLEXI_HOUSEKEEPER_STALE_JOB_AGE`` minutes.
   * - 3
     - **ScheduleIntegrity**
     - Resets stale ``next_schedule`` timestamps on RunTemplates that have no
       corresponding pending job, so the scheduler daemon picks them up again on
       its next tick.
   * - 4
     - **DataRetentionCleanup**
     - Enforces GDPR data retention policies. Delegates to
       ``MultiFlexi\DataRetention\RetentionService`` when ``multiflexi-web`` is
       installed; otherwise uses a built-in pass that reads the
       ``data_retention_policies`` table and applies ``hard_delete`` or
       ``soft_delete`` to expired rows in ``job``, ``log``, ``user_sessions``,
       and other tables.
   * - 5
     - **DiskTempFileCleanup**
     - Removes orphaned temporary result files from the MultiFlexi temp directory
       that are older than ``MULTIFLEXI_HOUSEKEEPER_TMP_AGE_HOURS`` hours and
       not referenced by any currently-running job.
   * - 6
     - **LogPruning**
     - Keeps the ``log`` table below ``MULTIFLEXI_HOUSEKEEPER_LOG_KEEP`` rows by
       deleting the oldest entries. Runs after all other duties so their log
       messages survive the prune.
   * - 7
     - **RuntemplateCounterRecalc**
     - Recalculates ``successfull_jobs_count`` and ``failed_jobs_count`` on all
       RunTemplates from the surviving job records. Corrects drift that
       accumulates as data retention deletes old job rows.
   * - 8
     - **CredentialHealthCheck**
     - Calls ``checkAvailability()`` on the prototype of each credential assigned
       to an active RunTemplate. Credentials returning ``Misconfigured`` are logged
       as warnings so operators can fix them before a job is blocked at runtime.
       This duty is read-only; dry-run has no additional effect.

Dry-Run Mode
------------

All duties support a non-destructive preview mode that logs what *would* be done
without making any database writes or deleting any files:

.. code-block:: bash

   # Run via the binary
   sudo -u multiflexi multiflexi-housekeeper --dry-run

   # Or via the env variable
   sudo -u multiflexi env MULTIFLEXI_HOUSEKEEPER_DRY_RUN=true \
     php /usr/lib/multiflexi-housekeeper/housekeeper.php

Dry-run output is identical to a real run except all log messages are prefixed
with ``[DRY-RUN]``.

Daemon Mode
-----------

By default the HouseKeeper runs once and exits (driven by the systemd timer). For
environments where a systemd timer is not available, it can run as a continuous
daemon:

.. code-block:: bash

   # In /etc/multiflexi/multiflexi.env
   MULTIFLEXI_DAEMONIZE=true
   MULTIFLEXI_HOUSEKEEPER_CYCLE_PAUSE=3600

Then start (and keep running) via the service unit:

.. code-block:: bash

   sudo systemctl start multiflexi-housekeeper.service

.. note::

   When ``MULTIFLEXI_DAEMONIZE=true``, disable the timer to avoid running both at
   the same time: ``sudo systemctl disable --now multiflexi-housekeeper.timer``

Configuration
-------------

All settings are read from ``/etc/multiflexi/multiflexi.env`` alongside the
standard ``DB_*`` and logging variables used by all MultiFlexi components.

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Variable
     - Default
     - Description
   * - ``MULTIFLEXI_DAEMONIZE``
     - ``false``
     - Run in continuous loop instead of exiting after one cycle.
   * - ``MULTIFLEXI_HOUSEKEEPER_DRY_RUN``
     - ``false``
     - Simulate all duties without database writes or file deletions.
   * - ``MULTIFLEXI_HOUSEKEEPER_CYCLE_PAUSE``
     - ``3600``
     - Seconds between cycles in daemon mode.
   * - ``MULTIFLEXI_HOUSEKEEPER_LOG_KEEP``
     - ``100000``
     - Maximum rows to retain in the ``log`` table (LogPruning duty).
   * - ``MULTIFLEXI_HOUSEKEEPER_TMP_AGE_HOURS``
     - ``24``
     - Minimum file age in hours before orphaned temp files are deleted.
   * - ``MULTIFLEXI_HOUSEKEEPER_STALE_JOB_AGE``
     - ``60``
     - Minutes after which an unstarted, unscheduled job is considered orphaned.
   * - ``MULTIFLEXI_HOUSEKEEPER_SKIP_DUTIES``
     - *(empty)*
     - Comma-separated list of duty class names to skip, e.g.
       ``CredentialHealthCheck,LogPruning``.
   * - ``MULTIFLEXI_HOUSEKEEPER_CREDENTIAL_CHECK``
     - ``true``
     - Set to ``false`` to disable the CredentialHealthCheck duty entirely.
   * - ``APP_DEBUG``
     - ``false``
     - Enable verbose console logging.

Viewing Logs
------------

.. code-block:: bash

   # Live log tail (timer-driven runs)
   sudo journalctl -u multiflexi-housekeeper.service -f

   # All runs since last boot
   sudo journalctl -u multiflexi-housekeeper.service -b

   # Timer activation history
   sudo journalctl -u multiflexi-housekeeper.timer

The HouseKeeper also writes structured log entries to the MultiFlexi ``log``
database table (component: ``housekeeper``) via the standard ``LogToSQL`` handler,
visible in the MultiFlexi web UI under System Logs.

Integration with Data Retention
--------------------------------

When ``multiflexi-web`` is installed, the **DataRetentionCleanup** duty delegates to
``MultiFlexi\DataRetention\RetentionService``, which enforces the full GDPR policy
set configured in the ``data_retention_policies`` table (manage via the web UI at
*Administration → Data Retention*).

Without ``multiflexi-web``, the duty falls back to a built-in minimal pass: it reads
the ``data_retention_policies`` table directly and applies ``hard_delete`` or
``soft_delete`` actions. The fallback covers the same policies but does not produce
compliance reports or archive data before deletion.

.. seealso::

   :doc:`../gdpr-compliance` — GDPR compliance overview and retention policy configuration

Skipping Individual Duties
--------------------------

During incidents or migrations you may want to disable a specific duty temporarily
without redeploying. Use ``MULTIFLEXI_HOUSEKEEPER_SKIP_DUTIES``:

.. code-block:: bash

   # Skip credential probing during a maintenance window
   echo "MULTIFLEXI_HOUSEKEEPER_SKIP_DUTIES=CredentialHealthCheck" \
     >> /etc/multiflexi/multiflexi.env
   sudo systemctl start multiflexi-housekeeper.service

   # Restore
   sed -i '/MULTIFLEXI_HOUSEKEEPER_SKIP_DUTIES/d' /etc/multiflexi/multiflexi.env

Troubleshooting
---------------

HouseKeeper completes instantly with no output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is normal — there may simply be nothing to clean up. Run with ``APP_DEBUG=true``
to see per-duty debug messages:

.. code-block:: bash

   sudo -u multiflexi env APP_DEBUG=true \
     php /usr/lib/multiflexi-housekeeper/housekeeper.php

DataRetentionCleanup duty is skipped
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``data_retention_policies`` table does not exist yet. Run the database
migrations:

.. code-block:: bash

   sudo -u multiflexi php /usr/share/multiflexi/vendor/bin/phinx migrate \
     -c /etc/multiflexi/phinx.php

CredentialHealthCheck reports false Misconfigured warnings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some credential prototypes read their field values via the ``configFieldsProvided``
collection which may not be populated outside the job execution context. If a
credential that works in practice is reported as misconfigured, suppress the check
for that prototype by adding its class to
``MULTIFLEXI_HOUSEKEEPER_SKIP_DUTIES`` or set
``MULTIFLEXI_HOUSEKEEPER_CREDENTIAL_CHECK=false``.

Timer not firing
~~~~~~~~~~~~~~~~

Check that the timer unit is enabled and that the system clock is correct:

.. code-block:: bash

   systemctl status multiflexi-housekeeper.timer
   systemctl list-timers multiflexi-housekeeper

See Also
--------

- :doc:`database-maintenance` — Manual database cleanup procedures
- :doc:`systemd-services` — Managing all MultiFlexi systemd units
- :doc:`../gdpr-compliance` — GDPR retention policies
- :doc:`../reference/configuration` — Full environment variable reference
