Systemd Services
================

**Target Audience:** Administrators
**Difficulty:** Beginner
**Prerequisites:** Basic Linux systemd knowledge

.. contents::
   :local:
   :depth: 2

Overview
--------

A standard MultiFlexi installation runs three continuously-running background services and one periodic maintenance timer managed by systemd:

+----------------------------------------------+----------------------------------------------+
| Service / Timer unit                         | Purpose                                      |
+==============================================+==============================================+
| ``multiflexi-scheduler.service``             | Enqueues jobs based on RunTemplate schedules |
+----------------------------------------------+----------------------------------------------+
| ``multiflexi-executor.service``              | Executes queued jobs                         |
+----------------------------------------------+----------------------------------------------+
| ``multiflexi-eventor.service``               | Triggers jobs in response to external events |
+----------------------------------------------+----------------------------------------------+
| ``multiflexi-housekeeper.timer`` (hourly)    | Periodic maintenance — cleanup, retention,   |
|                                              | schedule integrity, credential health checks |
+----------------------------------------------+----------------------------------------------+

All run as the ``multiflexi`` system user and load their configuration from ``/etc/multiflexi/multiflexi.env``.

Checking Service Status
------------------------

.. code-block:: bash

   # Status of all services at a glance
   systemctl status multiflexi-scheduler multiflexi-executor multiflexi-eventor

   # Detailed status with recent log lines
   systemctl status multiflexi-executor -l

   # HouseKeeper timer — next scheduled run
   systemctl list-timers multiflexi-housekeeper

Starting and Stopping Services
--------------------------------

.. code-block:: bash

   # Start
   sudo systemctl start multiflexi-scheduler
   sudo systemctl start multiflexi-executor
   sudo systemctl start multiflexi-eventor

   # Stop
   sudo systemctl stop multiflexi-executor

   # Restart (e.g. after configuration change)
   sudo systemctl restart multiflexi-executor

   # Reload (re-reads the env file without interrupting running jobs — executor only)
   sudo systemctl reload multiflexi-executor

   # Trigger an immediate HouseKeeper run without waiting for the timer
   sudo systemctl start multiflexi-housekeeper.service

Enabling / Disabling on Boot
-----------------------------

Services are enabled at boot by default after installation. To manage this:

.. code-block:: bash

   # Enable (start at boot)
   sudo systemctl enable multiflexi-executor

   # Disable
   sudo systemctl disable multiflexi-eventor

Viewing Logs
-------------

All services log to the systemd journal.

.. code-block:: bash

   # Live log tail
   sudo journalctl -u multiflexi-executor -f

   # All services together
   sudo journalctl -u multiflexi-scheduler -u multiflexi-executor -u multiflexi-eventor \
     -u multiflexi-housekeeper -f

   # Last 100 lines
   sudo journalctl -u multiflexi-executor -n 100

   # Logs since last boot
   sudo journalctl -u multiflexi-executor -b

   # Logs between timestamps
   sudo journalctl -u multiflexi-executor --since "2025-01-01 08:00" --until "2025-01-01 10:00"

Service Details
---------------

multiflexi-scheduler
~~~~~~~~~~~~~~~~~~~~~

Scans RunTemplates in the database and creates Job records when a scheduled run time is due. Runs continuously as a simple PHP daemon.

- **Binary**: ``/usr/lib/multiflexi-scheduler/daemon.php``
- **Restarts automatically**: yes (``Restart=always``, 10 s delay)
- **No memory ceiling** (scheduler is lightweight)

multiflexi-executor
~~~~~~~~~~~~~~~~~~~~

Picks up pending Job records, resolves environment variables, runs the job via the configured executor module, and stores results + artifacts.

- **Binary**: ``/usr/share/multiflexi-executor/daemon.php``
- **Memory ceiling**: 2 GB (``MemoryMax=2G``) — restarts automatically if exceeded
- **Soft memory warning**: 1800 MB (``MULTIFLEXI_MEMORY_LIMIT_MB=1800``)
- **Restarts automatically**: yes (``Restart=always``, 10 s delay)

multiflexi-eventor
~~~~~~~~~~~~~~~~~~~

Monitors configured event sources and enqueues jobs in response to external triggers (files, webhooks, queue messages).

- **Binary**: ``/usr/lib/multiflexi-eventor/daemon.php``
- **Memory ceiling**: 1 GB (``MemoryMax=1G``)
- **Restarts automatically**: yes (``Restart=always``, 10 s delay)

.. note::

   If you do not use event-driven job triggering, ``multiflexi-eventor`` can be disabled:
   ``sudo systemctl disable --now multiflexi-eventor``

multiflexi-housekeeper
~~~~~~~~~~~~~~~~~~~~~~~

Periodic maintenance timer that runs once per hour. Cleans orphaned jobs and broken
schedule entries, finalizes stale Tasks, enforces data retention policies, prunes the
log table, recalculates RunTemplate job counters, and checks credential health.

- **Package**: ``multiflexi-housekeeper``
- **Timer**: ``multiflexi-housekeeper.timer`` (``OnCalendar=hourly``, ``Persistent=true``)
- **Service**: ``multiflexi-housekeeper.service`` (``Type=oneshot``)
- **Binary**: ``/usr/lib/multiflexi-housekeeper/housekeeper.php``
- **Jitter**: up to 5 minutes (``RandomizedDelaySec=300``) — prevents thundering-herd on multi-server deployments
- **Dry-run**: ``sudo -u multiflexi multiflexi-housekeeper --dry-run``

.. note::

   The HouseKeeper uses a *timer* unit, not a continuously-running service.
   ``systemctl status multiflexi-housekeeper.service`` shows the result of the last
   run; ``systemctl list-timers multiflexi-housekeeper`` shows the next scheduled run.

See :doc:`housekeeper` for full configuration reference and troubleshooting.

Node-RED bridge
^^^^^^^^^^^^^^^

``multiflexi-eventor`` can forward webhook change events and finished jobs to a
Node-RED HTTP-in endpoint. The bridge is optional and disabled by default.

You are prompted for the bridge settings when the package is installed (debconf).
To reconfigure them later, run:

.. code-block:: bash

   sudo dpkg-reconfigure multiflexi-eventor

The answers are written to ``/etc/multiflexi/multiflexi.env``:

- **NODERED_WEBHOOK_URL**: Node-RED HTTP-in endpoint URL. Leave empty to disable the bridge.
- **NODERED_TOKEN**: Optional shared secret sent as the ``X-MultiFlexi-Token`` header.
- **NODERED_FORWARD_CHANGES**: Forward incoming webhook changes in addition to finished jobs (default: ``true``).

You can also set these variables directly in ``/etc/multiflexi/multiflexi.env``
and restart the service.

Node-RED catalog feed
^^^^^^^^^^^^^^^^^^^^^^

Beyond forwarding events, ``multiflexi-eventor`` can publish the MultiFlexi
*configuration catalog* — every company, every enabled run-template and every
credential — to the ``node-red-contrib-multiflexi`` **catalog** node. The
catalog node then builds one Node-RED palette node per entity, each carrying the
same icon it has in MultiFlexi.

Set these in ``/etc/multiflexi/multiflexi.env``:

- **NODERED_CATALOG_URL**: HTTP-in URL of the catalog node (e.g.
  ``http://node-red:1880/multiflexi-catalog``). Use a path distinct from
  ``NODERED_WEBHOOK_URL``. Leave empty to disable the feed.
- **NODERED_CATALOG_INTERVAL**: How often (seconds) to republish the catalog. The
  payload is content-hashed, so an unchanged catalog is not resent (default: ``300``).

The ``NODERED_TOKEN`` shared secret, when set, is also sent with the catalog push.

Icons are **not** embedded in the push. The catalog node fetches each entity's
icon from the MultiFlexi web image endpoints — ``appimage.php`` (apps),
``companylogo.php`` and ``credentialimage.php`` — which are public (no login).
On the catalog node, set **App URL** (``MULTIFLEXI_APP_URL``, default
``/multiflexi/``) to where the MultiFlexi web UI is reachable from Node-RED.
The ``node-red-contrib-multiflexi`` package also ships a systemd drop-in that
adds ``/usr/share/node-red`` to the Node-RED service ``NODE_PATH``.

Exposing the editor over HTTPS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Do not link users to the unencrypted ``:1880`` port. Instead, reverse-proxy the
Node-RED editor under a path on the existing HTTPS vhost (for example
``https://multiflexi.example.com/node-red/``). Tell Node-RED its base path so its
assets and admin API resolve behind the proxy, in ``settings.js``:

.. code-block:: javascript

   httpAdminRoot: '/node-red',

Then add an Apache reverse proxy (enable ``proxy``, ``proxy_http``,
``proxy_wstunnel`` and ``rewrite``):

.. code-block:: apache

   RewriteEngine On
   RewriteCond %{HTTP:Upgrade} =websocket [NC]
   RewriteRule ^/node-red/comms(.*)$ ws://127.0.0.1:1880/node-red/comms$1 [P,L]
   ProxyPass        /node-red/ http://127.0.0.1:1880/node-red/
   ProxyPassReverse /node-red/ http://127.0.0.1:1880/node-red/

The catalog HTTP-in node stays on the local port (its ``httpNodeRoot`` is left at
``/``), so ``NODERED_CATALOG_URL`` keeps pointing at ``http://127.0.0.1:1880/...``.
The ``vitexus.multiflexi`` Ansible ``multiflexi_server`` role configures all of
this automatically via ``multiflexi_server_nodered_http_root`` (default
``/node-red``).

Protect the editor with a login (``adminAuth`` in ``settings.js``). Generate a
bcrypt password hash with ``node-red-admin hash-pw`` and add a user:

.. code-block:: javascript

   adminAuth: {
       type: "credentials",
       users: [{ username: "demo", password: "$2b$12$...", permissions: "*" }]
   },

The Ansible role creates this demo user automatically
(``multiflexi_server_nodered_admin_user`` / ``_admin_password_hash`` /
``_admin_permissions``; default ``demo`` with full access — use ``read`` for a
read-only demo).

Configuration File
-------------------

All services share ``/etc/multiflexi/multiflexi.env``. After editing this file, restart the affected services:

.. code-block:: bash

   sudo systemctl restart multiflexi-scheduler multiflexi-executor multiflexi-eventor

The HouseKeeper reads the env file at the start of each timer-triggered run, so no
restart is needed for ``multiflexi-housekeeper`` — the next run picks up the changes
automatically.

See :doc:`../reference/configuration` for the full list of configuration variables.

Troubleshooting Service Issues
--------------------------------

Service fails to start
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check the last start attempt
   sudo journalctl -u multiflexi-executor -n 50

   # Verify the env file is readable
   sudo -u multiflexi cat /etc/multiflexi/multiflexi.env

   # Check PHP syntax
   php -l /usr/share/multiflexi-executor/daemon.php

Service keeps restarting
~~~~~~~~~~~~~~~~~~~~~~~~~

Usually caused by a database connection failure or missing PHP extension.

.. code-block:: bash

   # Watch restart loop
   sudo journalctl -u multiflexi-executor -f

   # Test database connectivity
   php -r "new PDO('mysql:host=127.0.0.1;dbname=multiflexi', 'user', 'pass');"

Jobs are not being executed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Verify the executor is running: ``systemctl status multiflexi-executor``
2. Verify the scheduler is running: ``systemctl status multiflexi-scheduler``
3. Check for pending jobs in the database:

   .. code-block:: bash

      multiflexi-cli job:list --status=pending

4. Check executor logs for errors: ``journalctl -u multiflexi-executor -n 200``

See Also
--------

- :doc:`../concepts/execution-architecture` — How the daemons interact
- :doc:`housekeeper` — HouseKeeper periodic maintenance reference
- :doc:`../reference/configuration` — Environment variables
- :doc:`../troubleshooting` — General troubleshooting guide
- :doc:`docker` — Running services in Docker Compose
