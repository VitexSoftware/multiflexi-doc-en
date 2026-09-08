Zabbix Integration
==================

MultiFlexi provides comprehensive integration with Zabbix for infrastructure monitoring, job execution tracking, and automated alerting. This integration enables real-time visibility into MultiFlexi operations and allows proactive incident management.

.. toctree::
   :maxdepth: 2

.. contents::
   :local:
   :depth: 3

Overview
--------

The MultiFlexi-Zabbix integration provides:

- **Job Execution Monitoring**: Track job success/failure rates, execution times, and status
- **Application Metrics**: Monitor application performance and availability
- **Company-Level Monitoring**: Track metrics per company/tenant
- **Low-Level Discovery (LLD)**: Automatic discovery of companies, applications, and run templates
- **Custom Metrics**: Send application-specific metrics from job output
- **Alerting**: Configure alerts based on job failures, execution times, or custom metrics

Architecture
------------

MultiFlexi communicates with Zabbix using two methods:

**1. Zabbix Sender Protocol** (recommended)
   - Native PHP implementation of Zabbix sender protocol
   - Direct TCP socket communication to Zabbix server (port 10051)
   - No external dependencies required
   - Real-time metric transmission

**2. Zabbix Sender Binary** (optional)
   - Uses system ``zabbix_sender`` command
   - Requires ``zabbix-sender`` package installation
   - Enabled with ``USE_ZABBIX_SENDER=true``

Data Flow:

.. code-block:: text

   MultiFlexi Job → Action Handler → ZabbixSender → Zabbix Server → Zabbix Database
                                                           ↓
                                                    Zabbix Frontend
                                                           ↓
                                                      Alerts/Graphs

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Configure Zabbix integration using environment variables in ``/etc/multiflexi/multiflexi.env`` or ``.env``:

.. code-block:: bash

   # Zabbix Server Configuration
   ZABBIX_SERVER=zabbix.example.com      # Zabbix server hostname or IP
   ZABBIX_HOST=multiflexi-server          # This MultiFlexi instance hostname in Zabbix
   
   # Optional: Use system zabbix_sender binary instead of native PHP sender
   USE_ZABBIX_SENDER=false                # Set to 'true' to use /usr/bin/zabbix_sender

**Variable Descriptions:**

- ``ZABBIX_SERVER``: The hostname or IP address of your Zabbix server/proxy. If not set, Zabbix integration is disabled.
- ``ZABBIX_HOST``: The monitored host name as registered in Zabbix. Defaults to system hostname if not specified. Can be overridden per-company.
- ``USE_ZABBIX_SENDER``: When ``true``, uses the system ``zabbix_sender`` binary instead of native PHP implementation.

Company-Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each company can override the Zabbix hostname using the ``zabbix_host`` field in the company configuration:

.. code-block:: bash

   multiflexi-cli company:update --id=1 --zabbix_host=customer-server

This allows multi-tenant deployments where different companies report to different Zabbix hosts.

Zabbix Server Setup
~~~~~~~~~~~~~~~~~~~

**1. Create Host in Zabbix**

Create a host in Zabbix matching your ``ZABBIX_HOST`` value:

- Host name: ``multiflexi-server`` (or your configured value)
- Monitored by: Zabbix server or proxy
- Interfaces: Not required (using passive items)

**2. Create Zabbix Trapper Items**

MultiFlexi sends metrics as Zabbix trapper items. For each metric, create a trapper item:

- Type: ``Zabbix trapper``
- Key: ``zabbix_action[{key}]`` (see Metric Keys section)
- Type of information: Text, Numeric, or Log depending on metric

**3. Import MultiFlexi Template** (recommended)

Import the provided Zabbix template from the `multiflexi-zabbix` repository. This template includes pre-configured items, triggers, and graphs.

.. code-block:: bash

   # Repository
   https://github.com/VitexSoftware/multiflexi-zabbix

The template includes:

- **System Status Items**: Database configuration, service status, entity counts
- **Job Monitoring**: Job execution status and statistics
- **Company Discovery**: Automatic discovery of companies/tenants
- **RunTemplate Discovery**: Application and company-specific job monitoring
- **Action Discovery**: Monitoring of Zabbix actions configured in RunTemplates
- **Credential Availability Discovery**: Per-credential endpoint availability, with severity-tiered alerting on misconfigured or unreachable credentials
- **Pre-configured Triggers**: Job failures, low success rates, service down alerts
- **Performance Graphs**: Entity statistics and job execution metrics
- **HTTP Tests**: Web interface availability monitoring

**Template Features:**

- Compatible with Zabbix 6.0+
- Low-Level Discovery (LLD) for dynamic monitoring
- Dependent items using JSONPath for efficient data extraction
- Value mapping for human-readable status
- Customizable macros for thresholds

**Importing the template:**

Via the Zabbix frontend: *Data collection → Templates → Import*, select
``zabbix/multiflexi-template.xml`` (installed to
``/usr/share/multiflexi/zabbix-templates/multiflexi-template.xml`` by the ``.deb`` package). Via the
API, ``configuration.import`` with ``format: "json"`` (or ``"xml"``) works the same way; a host and
template linkage rule set of at least
``{"templates": {"createMissing": true, "updateExisting": true}, "discoveryRules": {...}, "items": {...}, "triggers": {...}, "valueMaps": {...}}``
is enough for a first import.

The template only needs importing into a given Zabbix server once - after that, link it to as many
hosts as needed the normal way (*Host → Templates → Link new templates*, or ``host.update`` with a
``templates`` array via the API).

**If the host already runs another template with overlapping item keys** (for example, a
hand-maintained template that also happens to define ``multiflexi.appstatus`` or similar): Zabbix
will refuse to link this template as-is, reporting *"Cannot inherit item with key ... because an item
with the same key is already inherited from template ..."*. In that situation, either remove the
duplicate items from one of the two templates first, or - if only the credential-availability feature
is actually needed on that host - re-import a trimmed copy of this template containing just the
``multiflexi.credential.lld`` discovery rule (and its macros/value map), using
``discoveryRules``/``items``/``triggers``/``valueMaps`` import rules with ``deleteMissing: true`` to
prune everything else back out of that copy before linking it.

**Zabbix Agent Configuration:**

The Zabbix agent configuration and LLD scripts are now part of the dedicated `multiflexi-zabbix` package. Installation provides UserParameters at ``/etc/zabbix/zabbix_agent2.d/multiflexi.conf``:

- ``multiflexi.company.lld`` - Company discovery
- ``multiflexi.job.lld`` - Job/task discovery
- ``multiflexi.runtemplate.lld[*]`` - RunTemplate discovery
- ``multiflexi.action.lld`` - Action discovery
- ``multiflexi.appstatus`` - System status (JSON format)
- ``multiflexi.jobstatus`` - Job status summary (JSON format)
- ``multiflexi.queue`` - Currently queued jobs (JSON format)
- ``multiflexi.schedule.stale`` - Stale RunTemplate schedule watchdog (JSON format)
- ``multiflexi.credential.lld`` - Credential availability discovery
- ``multiflexi.credential.check[*]`` - Credential availability check result (JSON format), keyed by credential ID

Restart Zabbix agent after package installation:

.. code-block:: bash

   systemctl restart zabbix-agent2

What Gets Checked and Sent
---------------------------

Every item above is an **active** Zabbix agent check: the agent itself runs the underlying
``multiflexi-cli`` or ``multiflexi-zabbix-lld-*`` command on its own polling schedule and pushes the
result to the server - MultiFlexi never has to push anything or know the Zabbix server's address for
these to work (that's only needed for the separate trapper/action-based reporting described in
`Zabbix Action Configuration`_). This section documents exactly what each check inspects and the
shape of the data it reports.

``multiflexi.appstatus`` - overall system health
    Backed by ``multiflexi-cli status --format=json`` (default poll interval: 5 minutes). Reports one
    JSON object with:

    - ``version-cli`` / ``version-core`` - installed ``multiflexi-cli`` and ``multiflexi-core`` versions
    - ``db-migration`` - name and version of the most recently applied database migration
    - ``user`` - OS user the check ran as
    - ``php`` / ``os`` / ``memory`` - PHP version, OS name, and current PHP memory usage in bytes
    - ``companies`` / ``apps`` / ``runtemplates`` / ``topics`` / ``credentials`` / ``credential_types`` -
      row counts for each of these entities
    - ``jobs`` - a human-readable summary string: total job count plus counts for the last month/week/
      day/hour and the average jobs-per-minute over the last day
    - ``database`` - driver and connection info (for SQLite: file path, owner, group, and file mode; for
      MySQL/PostgreSQL: driver, connection status, server info, and server version)
    - ``encryption`` - ``disabled``, ``active (N keys)``, or a ``broken (...)``/``unknown (...)`` reason
      if the encryption subsystem is misconfigured
    - ``zabbix`` - ``disabled`` or ``"<ZABBIX_HOST> => <ZABBIX_SERVER>"`` showing this integration's own
      configured target
    - ``telemetry`` - OpenTelemetry export status (``disabled`` or the configured endpoint/protocol)
    - ``executor`` / ``scheduler`` - systemd unit status of ``multiflexi-executor.service`` and
      ``multiflexi-scheduler.service``
    - ``timestamp`` - ISO 8601 timestamp of when the check ran

    The template's ``MultiFlexi: Database Host``, ``MultiFlexi: Total Applications/Companies/
    RunTemplates/Jobs`` items are ``DEPENDENT`` items that extract single fields from this same JSON via
    JSONPath, so the underlying command only actually runs once per interval.

``multiflexi.jobstatus`` - job execution counters
    Backed by ``multiflexi-cli job:status --format=json`` (default poll interval: 1 minute). A single
    SQL aggregate query over the ``job`` table plus the current scheduler queue length, reporting:

    - ``total_jobs`` - all jobs ever recorded
    - ``successful_jobs`` / ``failed_jobs`` - jobs with exit code 0 vs. non-zero
    - ``incomplete_jobs`` - jobs with no exit code yet (still running, or never finished)
    - ``total_applications`` - distinct applications that have run at least one job
    - ``repeated_jobs`` - jobs that belong to a recurring (scheduled) RunTemplate
    - ``queue_length`` - jobs currently waiting to run

``multiflexi.queue`` - the queue itself
    Backed by ``multiflexi-cli queue:list --format=json``. Returns the full list of currently queued
    jobs (id, RunTemplate, application, company, and scheduled time for each), not just a count -
    useful for inspecting *what* is queued rather than just how much.

``multiflexi.schedule.stale`` / ``multiflexi.schedule.stale.count`` - stuck scheduling watchdog
    Backed by ``multiflexi-cli run-template:stale --format=json --tolerance-hours=6`` (default poll
    interval: 15 minutes). Under normal operation a RunTemplate's ``next_schedule`` column is only ever
    set for the brief window between a job being queued and finishing; if a job crashes, gets OOM-killed,
    or otherwise fails outside the normal fail path, ``next_schedule`` can be left stuck in the past and
    the RunTemplate silently drops out of the daily cron rotation. This check lists every active,
    recurring RunTemplate whose ``next_schedule`` is both non-null and more than the tolerance window
    (default 6h) in the past: ``{"count": N, "stale": [{"id", "name", "company_id", "next_schedule",
    "last_schedule"}, ...]}``. The dependent ``.count`` item extracts just ``count`` for the
    ``MultiFlexi: N RunTemplate(s) have a stale schedule`` trigger (**High** severity); the raw
    ``multiflexi.schedule.stale`` item holds the full per-RunTemplate detail for troubleshooting. Fix
    with ``multiflexi-cli queue:fix``.

``multiflexi.company.lld`` / ``multiflexi.job.lld`` / ``multiflexi.runtemplate.lld[*]`` / ``multiflexi.action.lld`` - structural discovery
    These don't report metrics themselves; they discover *what exists* (companies, scheduled tasks,
    per-company RunTemplates, and RunTemplates with a Zabbix success/fail action configured) so Zabbix
    can create per-entity items and triggers automatically. See `Available LLD Scripts`_ above for each
    one's exact output macros.

``multiflexi.credential.lld`` / ``multiflexi.credential.check[*]`` - per-credential availability
    See :ref:`credential-availability-monitoring` below for the full behavior, state values, and JSON
    shape - this is the most involved check, since it invokes each credential type's own
    ``checkAvailability()`` implementation (a live reachability check) where one exists, and falls back
    to a static required-field completeness check otherwise.

Usage
-----

Zabbix Action Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Zabbix integration is configured as a success or failure action in RunTemplates.

**Web Interface:**

1. Navigate to RunTemplate details
2. Click "Configure Actions"
3. Enable "Zabbix" for Success and/or Fail actions
4. Configure:
   - **Zabbix key**: Item key in Zabbix (supports macros: ``{COMPANY_CODE}``, ``{APP_CODE}``, ``{RUNTEMPLATE_ID}``)
   - **Metrics file**: Path to JSON file with metrics (optional, uses stdout if empty)

**CLI Configuration:**

.. code-block:: bash

   # Create RunTemplate with Zabbix action
   multiflexi-cli run-template:create \
     --name="Daily Backup" \
     --app_id=5 \
     --company_id=1 \
     --interv="@daily"
   
   # Configure actions via web interface or database

Metric Keys
~~~~~~~~~~~

Metric keys follow this pattern:

.. code-block:: text

   zabbix_action[{COMPANY_CODE}-{APP_CODE}-{RUNTEMPLATE_ID}-data]

**Examples:**

- ``zabbix_action[ACME-backup-42-data]`` - Company ACME, backup app, runtemplate 42
- ``zabbix_action[DEMO-invoice-sync-15-data]`` - Company DEMO, invoice sync app, runtemplate 15

**Custom Keys:**

You can override the default key in the Zabbix action configuration:

.. code-block:: text

   zabbix_action[custom-metric-name]

Sending Metrics
~~~~~~~~~~~~~~~

**Method 1: Standard Output**

By default, the Zabbix action sends job stdout to Zabbix:

.. code-block:: bash

   #!/bin/bash
   # Your application
   echo "Jobs processed: 150"
   echo "Errors: 0"
   echo "Duration: 5.2s"

This output is sent to Zabbix when the Zabbix action executes.

**Method 2: Metrics File**

For structured data, write a JSON file and specify it in the Zabbix action:

.. code-block:: json

   {
     "jobs_processed": 150,
     "errors": 0,
     "duration_seconds": 5.2,
     "status": "success"
   }

Configure the metrics file path:

- **Web UI**: Set "Metrics file" field to ``/tmp/metrics.json``
- **Application**: Define ``RESULT_FILE`` environment variable

**Method 3: Application Environment Variable**

Applications can define ``RESULT_FILE`` and ``ZABBIX_KEY`` in their JSON definition:

.. code-block:: json

   {
     "environment": {
       "RESULT_FILE": {
         "type": "file-path",
         "description": "Output metrics file",
         "defval": "/tmp/app-metrics.json",
         "required": false
       },
       "ZABBIX_KEY": {
         "type": "string",
         "description": "Zabbix item key",
         "defval": "app-custom-metric",
         "required": false
       }
     }
   }

Low-Level Discovery (LLD)
--------------------------

MultiFlexi provides LLD scripts for automatic discovery of monitoring entities in Zabbix.

Available LLD Scripts
~~~~~~~~~~~~~~~~~~~~~

**1. multiflexi-zabbix-lld**

Discovers companies:

.. code-block:: bash

   multiflexi-zabbix-lld

Output:

.. code-block:: json

   [
     {
       "{#COMPANY_NAME}": "Acme Corporation",
       "{#COMPANY_CODE}": "ACME",
       "{#COMPANY_SERVER}": "multiflexi-server"
     },
     {
       "{#COMPANY_NAME}": "Beta Industries",
       "{#COMPANY_CODE}": "BETA",
       "{#COMPANY_SERVER}": "multiflexi-server"
     }
   ]

With ``-a`` flag, discovers applications per company:

.. code-block:: bash

   multiflexi-zabbix-lld -a

Output includes:

- ``{#APPNAME}`` - Application name
- ``{#INTERVAL}`` - Execution interval (e.g., "hourly", "daily")
- ``{#COMPANY_NAME}`` - Company name
- ``{#COMPANY_CODE}`` - Company code/slug
- ``{#COMPANY_SERVER}`` - Zabbix host name

**2. multiflexi-zabbix-lld-company**

Discovers run templates for a specific company:

.. code-block:: bash

   multiflexi-zabbix-lld-company SERVER.COMPANY_CODE

Example:

.. code-block:: bash

   multiflexi-zabbix-lld-company multiflexi-server.ACME

Output:

.. code-block:: json

   [
     {
       "{#APPNAME}": "Invoice Sync",
       "{#APPNAME_CODE}": "invoice-sync",
       "{#APPNAME_UUID}": "a1b2c3d4-...",
       "{#INTERVAL}": "hourly",
       "{#INTERVAL_SECONDS}": "3600",
       "{#RUNTEMPLATE}": "15",
       "{#RUNTEMPLATE_NAME}": "Daily Invoice Sync",
       "{#COMPANY_NAME}": "Acme Corporation",
       "{#COMPANY_CODE}": "ACME",
       "{#COMPANY_SERVER}": "multiflexi-server"
     }
   ]

**3. multiflexi-zabbix-lld-actions**

Discovers run templates with Zabbix actions configured:

.. code-block:: bash

   multiflexi-zabbix-lld-actions

Output includes:

- ``{#RUN_TEMPLATE_ID}`` - RunTemplate ID
- ``{#RUN_TEMPLATE_NAME}`` - RunTemplate name
- ``{#COMPANY_ID}`` - Company ID
- ``{#COMPANY_NAME}`` - Company name
- ``{#APP_ID}`` - Application ID
- ``{#APP_NAME}`` - Application name
- ``{#SUCCESS_ACTIONS}`` - Serialized success actions
- ``{#FAIL_ACTIONS}`` - Serialized fail actions
- ``{#ZABBIX_KEY_SUCCESS}`` - Zabbix key for success
- ``{#ZABBIX_KEY_FAIL}`` - Zabbix key for failure

**4. multiflexi-zabbix-lld-tasks**

Discovers scheduled tasks/jobs.

**5. multiflexi-zabbix-lld-credentials**

Discovers MultiFlexi credentials and, per credential, checks their availability. See :ref:`credential-availability-monitoring` below for the full behavior.

.. code-block:: bash

   # Discovery mode
   multiflexi-zabbix-lld-credentials

   # Check mode: run one availability check for a given credential ID
   multiflexi-zabbix-lld-credentials 5

Discovery output:

.. code-block:: json

   [
     {
       "{#CREDENTIAL_ID}": 5,
       "{#CREDENTIAL_NAME}": "Acme FioBank CZK",
       "{#CREDENTIAL_TYPE}": "FioBank Acme Corporation",
       "{#COMPANY_ID}": 1,
       "{#COMPANY_NAME}": "Acme Corporation"
     }
   ]

Check output:

.. code-block:: json

   {
     "state": "available",
     "state_code": 0,
     "message": "",
     "checked_at": 1735689600,
     "ttl": 300,
     "details": []
   }

.. _credential-availability-monitoring:

Credential Availability Monitoring
-----------------------------------

Many :doc:`/credential-type` prototypes (AbraFlexi, FioBank, RaiffeisenBank, Pohoda mServer, Realpad, database connections, SMTP, VaultWarden, Office365, ...) implement a live ``checkAvailability()`` endpoint check. The **Credential Availability Discovery** rule (``multiflexi.credential.lld``) surfaces that state to Zabbix so failing or misconfigured credentials show up as alerts instead of only being noticed when a job using them fails.

**Discovery scope:** every credential is discovered, not only ones with a live check. A credential whose type has no ``checkAvailability()`` implementation is still evaluated against a generic fallback: if any of its required configuration fields is empty, it is reported ``Misconfigured`` (it cannot possibly work); otherwise it is reported ``Unknown`` (no way to verify without a live check).

**State values** (item ``multiflexi.credential.state[{#CREDENTIAL_ID}]``, mapped by the ``MultiFlexi Credential State`` value map):

- ``Available`` (0) - Endpoint reachable, credential usable. No trigger.
- ``Degraded`` (1) - Reachable but impaired (e.g. remote service busy or rate-limited). Trigger severity: **Average**.
- ``Unavailable`` (2) - Fully configured, but the endpoint could not be reached. Trigger severity: **High**.
- ``Misconfigured`` (3) - Required configuration field(s) missing or empty. Trigger severity: **Warning**.
- ``Unknown`` (4) - No live check implemented, but required fields are filled. No trigger.

**Item structure:** to avoid running the (possibly network- or DB-bound) check more than once per polling cycle, each discovered credential gets one active ``TEXT`` master item, ``multiflexi.credential.check[{#CREDENTIAL_ID}]``, returning the full check result as JSON. Three dependent items extract from it via JSONPath preprocessing:

- ``multiflexi.credential.state[{#CREDENTIAL_ID}]`` - ``$.state_code`` (``UNSIGNED``, value-mapped)
- ``multiflexi.credential.message[{#CREDENTIAL_ID}]`` - ``$.message`` (``TEXT``, human-readable)
- ``multiflexi.credential.details[{#CREDENTIAL_ID}]`` - ``$.details`` (``TEXT``, opaque JSON)

The ``details`` field is intentionally passed through unchanged: every credential prototype puts different, sometimes localized, keys in it (there is no standardized schema across prototypes), so it is only meant for troubleshooting - not for alerting or dashboards.

**Configuring polling interval and exceptions per service:**

Some services have tight API rate limits (e.g. RaiffeisenBank's PSD2 API), so polling them as often as other credentials could exhaust their quota. This is handled entirely through template macros - no code change is needed when a new rate-limited credential type is added:

- ``{$CRED.AVAILABILITY.INTERVAL}`` (default ``5m``) - polling interval for ``multiflexi.credential.check[*]``. Override per credential type with a macro context, e.g. set ``{$CRED.AVAILABILITY.INTERVAL:"RaiffeisenBank"}`` to ``30m`` on the host.
- ``{$CRED.AVAILABILITY.EXCLUDE}`` (default ``^$``) - regex matched against ``{#CREDENTIAL_TYPE}``; any matching type is excluded from discovery entirely. The default only matches an empty string, which no real credential type name ever is, so nothing is excluded. E.g. set to ``^(SomeRateLimitedType)$`` to stop monitoring it. Do not set this to an empty string - an empty regex matches everything and would silently exclude every credential from discovery.

Both macros can be overridden at the host level in the Zabbix frontend, so exceptions for a specific deployment don't require editing the template.

Zabbix LLD Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

In Zabbix, create a discovery rule:

**Item Configuration:**

- Name: ``MultiFlexi Companies Discovery``
- Type: ``External check``
- Key: ``multiflexi-zabbix-lld``
- Type of information: ``Text``
- Update interval: ``1h``

**Item Prototypes:**

Create item prototypes using discovered macros:

.. code-block:: text

   # Company status item
   Key: zabbix_action[{#COMPANY_CODE}-status]
   Name: Company {#COMPANY_NAME} Status
   
   # Application metrics
   Key: zabbix_action[{#COMPANY_CODE}-{#APPNAME_CODE}-data]
   Name: {#COMPANY_NAME} - {#APPNAME} Metrics

**Trigger Prototypes:**

.. code-block:: text

   # Alert on job failure
   Expression: {MultiFlexi:zabbix_action[{#COMPANY_CODE}-{#APPNAME_CODE}-status].str("failed")}=1
   Severity: High
   Name: Job failed for {#COMPANY_NAME} - {#APPNAME}

Monitoring Examples
-------------------

Basic Job Monitoring
~~~~~~~~~~~~~~~~~~~~

Monitor job execution with exit code tracking:

**Application Script:**

.. code-block:: bash

   #!/bin/bash
   # Your job logic
   if [ $? -eq 0 ]; then
     echo "success"
     exit 0
   else
     echo "failed"
     exit 1
   fi

**Zabbix Configuration:**

- Enable Zabbix action for both Success and Fail
- Success key: ``zabbix_action[{COMPANY_CODE}-{APP_CODE}-{RUNTEMPLATE_ID}-success]``
- Fail key: ``zabbix_action[{COMPANY_CODE}-{APP_CODE}-{RUNTEMPLATE_ID}-fail]``

Advanced Metrics
~~~~~~~~~~~~~~~~

Send detailed performance metrics:

**Application Output (metrics.json):**

.. code-block:: json

   {
     "timestamp": "2025-01-30T12:00:00Z",
     "records_processed": 1523,
     "processing_time_ms": 4521,
     "memory_peak_mb": 128.5,
     "errors": 0,
     "warnings": 3,
     "status": "completed"
   }

**Zabbix Items:**

Create dependent items to extract specific fields:

.. code-block:: text

   Master item: zabbix_action[company-app-metrics]
   
   Dependent item: Records Processed
   Preprocessing: JSONPath: $.records_processed
   
   Dependent item: Processing Time
   Preprocessing: JSONPath: $.processing_time_ms
   Units: ms
   
   Dependent item: Memory Usage
   Preprocessing: JSONPath: $.memory_peak_mb
   Units: MB

Multi-Company Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~

Monitor multiple companies with separate Zabbix hosts:

**Company A Configuration:**

.. code-block:: bash

   multiflexi-cli company:update --id=1 --zabbix_host=customer-a-server

**Company B Configuration:**

.. code-block:: bash

   multiflexi-cli company:update --id=2 --zabbix_host=customer-b-server

Each company's metrics are sent to their respective Zabbix host.

Troubleshooting
---------------

Checking Zabbix Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify Zabbix configuration:

.. code-block:: bash

   multiflexi-cli status

Output shows:

.. code-block:: text

   zabbix: multiflexi-server => zabbix.example.com

Or if disabled:

.. code-block:: text

   zabbix: disabled

Testing Connectivity
~~~~~~~~~~~~~~~~~~~~

Test Zabbix server connectivity:

.. code-block:: bash

   # Test with system zabbix_sender
   zabbix_sender -z zabbix.example.com -s multiflexi-server -k test.key -o "test value"
   
   # Check Zabbix server port
   telnet zabbix.example.com 10051
   nc -zv zabbix.example.com 10051

Debugging Failed Sends
~~~~~~~~~~~~~~~~~~~~~~

**Enable Debug Logging:**

.. code-block:: bash

   # In /etc/multiflexi/multiflexi.env
   MULTIFLEXI_DEBUG=true
   EASE_LOGGER="syslog|\MultiFlexi\LogToSQL"

**Check Logs:**

.. code-block:: bash

   # System logs
   tail -f /var/log/syslog | grep -i zabbix
   
   # MultiFlexi database logs
   multiflexi-cli job:get --id=JOBID

**Common Issues:**

1. **"No Zabbix server defined"**
   - ``ZABBIX_SERVER`` not set in environment
   - Solution: Configure ``ZABBIX_SERVER`` in ``.env``

2. **"can't connect to zabbix.example.com:10051"**
   - Network connectivity issue
   - Firewall blocking port 10051
   - Incorrect server address
   - Solution: Check network, firewall rules, verify server address

3. **"Required metrics file not found"**
   - Metrics file path doesn't exist
   - Application didn't create the file
   - Solution: Verify file path, check application logs

4. **"zabbix server returned non-successful response"**
   - Zabbix host doesn't exist
   - Item key doesn't exist or wrong type
   - Solution: Create host/item in Zabbix, verify key names

Verifying Data in Zabbix
~~~~~~~~~~~~~~~~~~~~~~~~~

**Check Latest Data:**

1. Zabbix Frontend → Monitoring → Latest data
2. Select host (e.g., ``multiflexi-server``)
3. Filter by application or item name
4. Verify data is arriving

**Check Item History:**

1. Click on item name in Latest data
2. View → History
3. Verify timestamps and values

**Zabbix Server Logs:**

.. code-block:: bash

   tail -f /var/log/zabbix/zabbix_server.log | grep -i trapper

Discovery Rule Produces No Items After Linking the Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Active-check discovery rules (all of the ``*.lld`` items in this package) are pulled by the Zabbix
*agent*, not pushed by the server, so the server has to hand the new key to the agent before anything
runs. Two independent causes can delay or block that, and both look identical from the outside (no
discovered items, no error):

1. **Server configuration cache staleness.** Zabbix server only rebuilds its active-checks list for a
   host periodically (``CacheUpdateFrequency``). Newly linking a template can take longer than expected
   to actually reach the agent. Confirm by tailing the agent's own log
   (``/var/log/zabbix/zabbix_agent2.log``) for the discovery key (e.g. ``multiflexi.credential.lld``) -
   if it never appears despite the agent's ``refreshActiveChecks()`` running every few seconds, the
   server hasn't offered it yet. Forcing a targeted resync (rather than waiting out
   ``CacheUpdateFrequency``): toggle the discovery rule's ``status`` off then back on via the API
   (``discoveryrule.update``) and restart ``zabbix-agent2`` on the host - this reliably triggers an
   immediate pickup.
2. **A misconfigured discovery filter silently excluding everything.** If the discovery rule's item
   count stays at zero even after the key does start executing (visible in the agent log with real
   JSON output), check the discovery rule's filter conditions. In particular, an empty string used as a
   ``NOT_MATCHES_REGEX`` pattern matches *everything* (an empty regex trivially matches at every
   position), which inverts to *excluding* every discovered row - this is why
   ``{$CRED.AVAILABILITY.EXCLUDE}`` defaults to ``^$`` rather than an empty string (see `What Gets
   Checked and Sent`_ above).

Neither of these produces a Zabbix-visible error; the only symptom is "the item just never shows up",
so when a freshly-linked discovery rule stays empty, check the agent log for actual execution first,
then double-check any filter macros before assuming the deployment is broken.

Best Practices
--------------

Metric Naming
~~~~~~~~~~~~~

- Use consistent naming: ``{COMPANY_CODE}-{APP_CODE}-{METRIC_TYPE}``
- Avoid special characters in keys
- Use descriptive names: ``backup-success`` instead of ``bs``
- Document custom keys in application JSON

Data Format
~~~~~~~~~~~

- Use JSON for structured metrics
- Include timestamp in ISO 8601 format
- Include status/severity field
- Keep metrics focused and relevant
- Don't send overly verbose output

Performance
~~~~~~~~~~~

- Batch metrics when possible
- Use metrics files for large datasets
- Avoid sending binary data
- Consider data retention in Zabbix
- Monitor Zabbix server load

Security
~~~~~~~~

- Use Zabbix PSK encryption for sensitive data
- Restrict Zabbix server port (10051) access
- Validate metric data before sending
- Don't include passwords in metrics
- Use separate Zabbix hosts for multi-tenant deployments

Maintenance
~~~~~~~~~~~

- Regularly review Zabbix triggers
- Archive old metrics
- Update LLD rules when adding companies/apps
- Test monitoring after MultiFlexi upgrades
- Document custom Zabbix configurations

Comparison with OpenTelemetry
------------------------------

MultiFlexi supports both Zabbix and OpenTelemetry for monitoring. Choose based on your needs:

**Zabbix:**

- ✅ Mature, proven monitoring solution
- ✅ Comprehensive alerting and escalation
- ✅ Built-in frontend and dashboards
- ✅ LLD for automatic discovery
- ✅ Better for infrastructure monitoring
- ❌ More complex setup
- ❌ Less modern observability features

**OpenTelemetry:**

- ✅ Modern, vendor-neutral standard
- ✅ Cloud-native and microservices-friendly
- ✅ Better for metrics, traces, logs (3 pillars)
- ✅ Integration with Prometheus, Grafana, etc.
- ✅ Simpler metric export
- ❌ Requires separate components (collector, backend)
- ❌ Less mature alerting (depends on backend)

**Recommendation:**

- Use **Zabbix** if you already have Zabbix infrastructure and need comprehensive alerting
- Use **OpenTelemetry** for cloud-native deployments or Prometheus/Grafana stacks
- Use **both** for comprehensive observability (infrastructure + application metrics)

See Also
--------

- :doc:`/integrations/opentelemetry` - OpenTelemetry integration documentation
- :doc:`/reference/configuration` - General configuration options
- :doc:`/apps_overview` - Application development guide (including metrics)
- :doc:`/reference/cli` - CLI commands including status checking
- `Zabbix Documentation <https://www.zabbix.com/documentation/current/>`_
- `Zabbix Sender Protocol <https://www.zabbix.com/documentation/current/en/manual/appendix/protocols/header_datalen>`_

Reference Implementation
------------------------

The MultiFlexi Zabbix integration source code:

- **Action Handler**: ``php-vitexsoftware-multiflexi-core/src/MultiFlexi/Action/Zabbix.php``
- **Zabbix Sender**: ``php-vitexsoftware-multiflexi-core/src/MultiFlexi/ZabbixSender.php``
- **LLD Scripts & Templates**: ``https://github.com/VitexSoftware/multiflexi-zabbix``
- **Protocol Implementation**: ``php-vitexsoftware-multiflexi-core/src/MultiFlexi/Zabbix/``

For development and customization examples, refer to the source code repository.

