.. _docker-executor-integration:

Docker Executor
===============


.. image:: ../_static/images/components/multiflexi-executor-docker.svg
   :width: 96px
   :align: right
   :alt: multiflexi-executor-docker

.. contents::
   :local:
   :depth: 2

MultiFlexi can execute jobs inside **Docker containers** using the Docker
executor (package ``multiflexi-executor-docker``).

When a runtemplate uses this executor, the ``multiflexi-executor`` daemon runs:

.. code-block:: text

   docker run --rm --env-file <tmp.env> [--network=…] --entrypoint <executable> <ociimage> <cmdparams>

Stdout and stderr are captured into the job record. The temporary env file is
removed after the run.

.. note::

   This page describes the **Docker job executor** (running application jobs
   *inside* containers). For deploying the MultiFlexi *stack* itself with
   Docker Compose, see :doc:`/administration/docker`.

Deployment checklist
--------------------

Do these steps **once per MultiFlexi host** that should run Docker jobs.

.. list-table::
   :header-rows: 1
   :widths: 8, 55, 37

   * - #
     - Step
     - Where
   * - 1
     - Install Docker Engine (``docker`` in ``$PATH``, daemon running)
     - Executor host
   * - 2
     - Install ``multiflexi-executor`` and ``multiflexi-executor-docker``
     - Executor host
   * - 3
     - Confirm user ``multiflexi`` is in group ``docker`` (postinst does this)
     - Executor host
   * - 4
     - Optional: set ``MULTIFLEXI_DOCKER_NETWORK`` / ``MULTIFLEXI_DOCKER_PULL``
     - ``/etc/multiflexi/multiflexi.env``
   * - 5
     - Restart ``multiflexi-executor`` so group membership takes effect
     - Executor host
   * - 6
     - Ensure the application has ``ociimage`` (required)
     - MultiFlexi DB / app JSON
   * - 7
     - Set the runtemplate ``executor`` to ``Docker``
     - MultiFlexi DB / CLI / UI
   * - 8
     - Schedule a job and verify stdout / exit code
     - Executor host

Step-by-step host setup
-----------------------

1. Install Docker Engine
~~~~~~~~~~~~~~~~~~~~~~~~

The ``docker`` CLI must talk to a running Docker daemon. On Debian/Ubuntu:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo systemctl enable --now docker
   docker version

Rootless Docker is possible but not covered here; the packaged postinst expects
the classic ``docker`` group socket access model.

2. Install MultiFlexi packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo apt-get install -y multiflexi-executor multiflexi-executor-docker

Confirm the class is present:

.. code-block:: bash

   ls -la /usr/share/php/MultiFlexi/Executor/Docker.php

3. Docker group membership
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``multiflexi-executor-docker`` postinst adds the ``multiflexi`` system user
to the ``docker`` group when both exist:

.. code-block:: bash

   getent group docker
   id multiflexi

Expected: ``groups=…,docker,…`` (or at least ``docker`` listed).

Group changes apply to **new** processes only. Restart the daemon:

.. code-block:: bash

   sudo systemctl restart multiflexi-executor

Verify the service can call Docker:

.. code-block:: bash

   sudo -u multiflexi docker info >/dev/null && echo OK

If this fails with permission denied on ``/var/run/docker.sock``, fix group
membership and restart again.

4. Optional environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit ``/etc/multiflexi/multiflexi.env`` (loaded by the systemd unit):

.. code-block:: bash

   # Attach containers to a named network (default: Docker bridge)
   # MULTIFLEXI_DOCKER_NETWORK=multiflexi_net

   # Pull the image before every job (always|true|1). Default: do not pull.
   # MULTIFLEXI_DOCKER_PULL=always

See also :doc:`/confienv` and :doc:`/reference/configuration`.

Then:

.. code-block:: bash

   sudo systemctl restart multiflexi-executor

Application configuration
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 20, 15, 65

   * - Field
     - Required?
     - Purpose
   * - ``ociimage``
     - **Yes**
     - Image passed to ``docker run`` (for example
       ``docker.io/vitexsoftware/multiflexi-probe:latest``)
   * - ``executable``
     - Recommended
     - Passed as ``--entrypoint`` inside the container
   * - ``cmdparams``
     - Optional
     - Arguments after the image name

``usableForApp()`` only checks that ``ociimage`` is non-empty.

Host file-type configuration fields are **not** injected as paths into the
container (they would point at executor-host filesystem paths). The executor
logs a warning and skips them.

Configuring a RunTemplate
-------------------------

.. code-block:: bash

   multiflexi-cli run-template:update --id=158 --executor=Docker

Or create a new runtemplate with ``--executor=Docker``.

Schedule immediately:

.. code-block:: bash

   multiflexi-cli run-template:schedule --id=158 --schedule_time=now

Execution flow
--------------

1. Check that ``docker`` exists and ``ociimage`` is set
2. Optionally ``docker pull <ociimage>`` when ``MULTIFLEXI_DOCKER_PULL`` is enabled
3. Write a temporary env file from the job environment
4. Run ``docker run --rm --env-file … --entrypoint … <image> …``
5. Capture stdout/stderr and exit code onto the job
6. Delete the temporary env file (``--rm`` already removes the container)

Verification
------------

.. code-block:: bash

   dpkg -l multiflexi-executor multiflexi-executor-docker
   id multiflexi | tr ',' '\n' | grep docker
   systemctl is-active multiflexi-executor
   sudo -u multiflexi docker info >/dev/null && echo docker_ok

After a job:

.. code-block:: bash

   multiflexi-cli job:get --id=<JOB_ID> --format=json

Check ``executor`` is ``Docker``, ``exitcode``, ``stdout``, and ``command``
(should start with ``docker run --rm``).

Troubleshooting
---------------

Permission denied on docker.sock
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``multiflexi`` must be in group ``docker``
- Restart ``multiflexi-executor`` after changing groups
- Confirm the socket exists: ``ls -l /var/run/docker.sock``

Image pull / not found
~~~~~~~~~~~~~~~~~~~~~~

- Verify ``ociimage`` is correct and reachable from the host
- Set ``MULTIFLEXI_DOCKER_PULL=always`` if the host should refresh tags
- Log in to private registries as needed for the ``multiflexi`` user context

Executor falls back to Native
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Package ``multiflexi-executor-docker`` installed
- Runtemplate ``executor`` is exactly ``Docker``
- ``sudo systemctl restart multiflexi-executor``
