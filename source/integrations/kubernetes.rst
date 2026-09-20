.. _kubernetes-integration:

Kubernetes Integration
======================


.. image:: ../_static/images/components/multiflexi-executor-k8s.svg
   :width: 96px
   :align: right
   :alt: multiflexi-executor-k8s

.. contents::
   :local:
   :depth: 2

MultiFlexi can execute jobs inside Kubernetes pods using the **Kubernetes
executor** (package ``multiflexi-executor-k8s``).

When a runtemplate uses this executor, the ``multiflexi-executor`` daemon:

1. Optionally deploys the application's Helm chart (only when ``helmchart`` is
   set and the release is not already present)
2. Remaps host ``MULTIFLEXI_TMP`` (and env values under it) to ``/tmp`` inside
   the pod
3. Launches a one-shot pod (``--attach --rm``, or a hold-and-``kubectl cp``
   path when the application declares ``artifacts``)
4. Captures stdout/stderr into the job record
5. Copies files matching ``app_artifacts`` path patterns into host
   ``MULTIFLEXI_TMP`` so ``Job::runEnd()`` can store them in the ``artifacts``
   table (same path as the Native executor)

This page is the full deployment and configuration guide.

Deployment checklist
--------------------

Do these steps **once per MultiFlexi host** that should run Kubernetes jobs,
and **once per cluster** for namespace/RBAC.

.. list-table::
   :header-rows: 1
   :widths: 8, 55, 37

   * - #
     - Step
     - Where
   * - 1
     - Install ``multiflexi-executor`` and ``multiflexi-executor-k8s``
     - Executor host
   * - 2
     - Install ``kubectl`` (and ``helm`` if you use Helm charts)
     - Executor host
   * - 3
     - Create namespace ``multiflexi`` (or your chosen name)
     - Cluster
   * - 4
     - Apply packaged RBAC (ServiceAccount + Role + RoleBinding)
     - Cluster
   * - 5
     - Mint a kubeconfig for SA ``multiflexi-executor``
     - Admin workstation → cluster
   * - 6
     - Install kubeconfig as ``/var/lib/multiflexi/.kube/config`` (mode ``0600``)
     - Executor host
   * - 7
     - Set ``KUBECONFIG`` and ``MULTIFLEXI_K8S_NAMESPACE`` in ``multiflexi.env``
     - Executor host
   * - 8
     - Ensure the application has ``ociimage`` (required) and optional
       ``helmchart`` / ``artifacts``
     - MultiFlexi DB / app JSON
   * - 9
     - Set the runtemplate ``executor`` to ``Kubernetes``
     - MultiFlexi DB / CLI / UI
   * - 10
     - Restart ``multiflexi-executor`` and verify with a scheduled job
     - Executor host

Step-by-step host and cluster setup
-----------------------------------

1. Install packages
~~~~~~~~~~~~~~~~~~

On the machine that runs the daemon (typically as the ``multiflexi`` system
user via systemd):

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install -y multiflexi-executor multiflexi-executor-k8s

Confirm the executor class and RBAC manifest are present:

.. code-block:: bash

   ls -la /usr/share/php/MultiFlexi/Executor/Kubernetes.php
   ls -la /usr/share/multiflexi/k8s/multiflexi-executor-rbac.yaml

2. Install kubectl and helm
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **kubectl** is mandatory (in ``$PATH`` for the daemon).
- **helm** (v3+) is required only when applications declare a ``helmchart``.
  One-shot pods without Helm work with kubectl alone.

On Debian/Ubuntu, ``kubectl`` is often available as package ``kubernetes-client``
or via your cluster vendor's repo. Install ``helm`` from your preferred source
if the distro does not ship it.

Verify as root (or any login that can see ``$PATH``):

.. code-block:: bash

   command -v kubectl
   command -v helm   # optional unless you use Helm charts
   kubectl version --client

3. Create the namespace
~~~~~~~~~~~~~~~~~~~~~~~

From a machine that already has cluster-admin (or equivalent) access:

.. code-block:: bash

   export KUBECONFIG=/path/to/admin.kubeconfig
   kubectl create namespace multiflexi

Use a different name only if you will also set ``MULTIFLEXI_K8S_NAMESPACE`` to
that same value on every executor host.

4. Apply RBAC
~~~~~~~~~~~~~

The ``multiflexi-executor-k8s`` package ships a least-privilege Role for
one-shot pods (create/get/list/watch/delete, logs, attach, exec) plus Helm
resources (deployments, replicasets, configmaps, secrets, serviceaccounts,
services) in namespace ``multiflexi``.

.. code-block:: bash

   kubectl apply -f /usr/share/multiflexi/k8s/multiflexi-executor-rbac.yaml

This creates:

- ServiceAccount ``multiflexi-executor``
- Role ``multiflexi-executor-role``
- RoleBinding ``multiflexi-executor-binding``

Verify:

.. code-block:: bash

   kubectl get sa,role,rolebinding -n multiflexi
   kubectl auth can-i create pods -n multiflexi \
     --as=system:serviceaccount:multiflexi:multiflexi-executor

Do **not** bind the Role to the ``default`` ServiceAccount and expect the
daemon to pick it up. The daemon authenticates with whatever identity is in
its kubeconfig file. Use the dedicated ``multiflexi-executor`` SA.

5. Create a ServiceAccount kubeconfig
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate a token-based kubeconfig for SA ``multiflexi-executor`` (example for
Kubernetes 1.24+, one-year token):

.. code-block:: bash

   export KUBECONFIG=/path/to/admin.kubeconfig
   SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
   CA=$(kubectl config view --raw --minify --flatten \
     -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
   TOKEN=$(kubectl create token multiflexi-executor -n multiflexi --duration=8760h)

   cat > multiflexi-executor.kubeconfig <<EOF
   apiVersion: v1
   kind: Config
   clusters:
   - cluster:
       certificate-authority-data: ${CA}
       server: ${SERVER}
     name: multiflexi
   contexts:
   - context:
       cluster: multiflexi
       namespace: multiflexi
       user: multiflexi-executor
     name: multiflexi-executor
   current-context: multiflexi-executor
   users:
   - name: multiflexi-executor
     user:
       token: ${TOKEN}
   EOF
   chmod 600 multiflexi-executor.kubeconfig

Smoke-test **before** copying to the host:

.. code-block:: bash

   KUBECONFIG=./multiflexi-executor.kubeconfig kubectl get pods -n multiflexi
   KUBECONFIG=./multiflexi-executor.kubeconfig helm -n multiflexi list

.. note::

   Prefer this SA kubeconfig over copying a cluster-admin kubeconfig onto the
   executor host. Renew the token before expiry (or use a longer-lived SA
   secret if your cluster policy allows it).

6. Install the kubeconfig on the executor host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The systemd unit runs as user ``multiflexi`` with home
``/var/lib/multiflexi/``. Place the kubeconfig there:

.. code-block:: bash

   sudo mkdir -p /var/lib/multiflexi/.kube
   sudo install -o multiflexi -g multiflexi -m 0600 \
     ./multiflexi-executor.kubeconfig \
     /var/lib/multiflexi/.kube/config

Verify as the daemon user:

.. code-block:: bash

   sudo -u multiflexi \
     KUBECONFIG=/var/lib/multiflexi/.kube/config \
     kubectl get pods -n multiflexi

7. Configure environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit ``/etc/multiflexi/multiflexi.env`` (loaded by
``multiflexi-executor.service`` via ``EnvironmentFiles=``) and add:

.. code-block:: bash

   KUBECONFIG=/var/lib/multiflexi/.kube/config
   MULTIFLEXI_K8S_NAMESPACE=multiflexi

Meaning:

- **KUBECONFIG** – absolute path to the SA kubeconfig. Without it, the
  executor falls back to ``$HOME/.kube/config`` for the process user
  (``/var/lib/multiflexi/.kube/config`` when HOME is set correctly).
- **MULTIFLEXI_K8S_NAMESPACE** – target namespace for pods and Helm. Overrides
  the Helm default namespace (``multiflexi`` when a chart is configured).
  When unset and no Helm chart is used, the cluster default namespace applies.

See also :doc:`/confienv` and :doc:`/reference/configuration`.

8. Restart the daemon
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo systemctl restart multiflexi-executor
   systemctl is-active multiflexi-executor
   systemctl status multiflexi-executor --no-pager

Application configuration
-------------------------

Required and optional application fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20, 15, 65

   * - Field
     - Required?
     - Purpose
   * - ``ociimage``
     - **Yes**
     - Container image for ``kubectl run`` (for example
       ``docker.io/vitexsoftware/multiflexi-probe``)
   * - ``helmchart``
     - No
     - When set, the executor runs ``helm upgrade --install`` if the release
       is missing. When empty, only the one-shot pod is launched.
   * - ``artifacts``
     - No
     - Comma-separated paths **inside the pod**. Every path is copied with
       ``kubectl cp`` and stored in the job file store (field name = file
       basename).
   * - ``executable`` / ``cmdparams``
     - As for Native
     - Command run inside the pod after ``--`` on ``kubectl run``

``usableForApp()`` only checks that ``ociimage`` is non-empty. A missing
``helmchart`` is valid.

Helm chart reference
~~~~~~~~~~~~~~~~~~~~

When ``helmchart`` is set, it may be:

- A local filesystem path readable by the ``multiflexi`` user
  (for example ``/opt/helm-charts/my-app``)
- An OCI registry reference (for example ``oci://ghcr.io/org/charts/my-app``)
- A Helm repository chart name (for example ``myrepo/my-app``)

You can set it via application JSON import or directly in the database:

.. code-block:: bash

   multiflexi-cli application:import-json --file=multiflexi/myapp.multiflexi.app.json

.. code-block:: sql

   UPDATE apps SET helmchart='/opt/helm-charts/my-app' WHERE id=23;

Example fragment in ``*.multiflexi.app.json`` (imported fields map to DB
columns; runtime currently derives config from ``helmchart``, ``name``, and
``artifacts``):

.. code-block:: json

   {
     "ociimage": "docker.io/example/my-app:latest",
     "kubernetes": {
       "helm": {
         "enabled": true,
         "chart": "oci://ghcr.io/example/my-app",
         "namespace": "multiflexi"
       },
       "artifacts": {
         "enabled": true,
         "outputPath": "report.json,output.csv"
       }
     }
   }

Release name is derived as a DNS-1123-safe form of the application ``name``
(max 63 characters), defaulting to ``mf-app``.

Helm chart structure
~~~~~~~~~~~~~~~~~~~~

A typical chart for a MultiFlexi application includes ConfigMap, Secret,
Deployment (with ``envFrom``), and optionally a ServiceAccount. See the
``multiflexi-probe`` project's ``helm/`` directory for a reference.

Configuring a RunTemplate
-------------------------

Set the executor on an existing runtemplate:

.. code-block:: bash

   multiflexi-cli run-template:update --id=158 --executor=Kubernetes

Or create a new one:

.. code-block:: bash

   multiflexi-cli run-template:create \
     --app_id=23 \
     --company_id=3 \
     --name="Probe via K8s" \
     --executor=Kubernetes \
     --interv=d \
     --cron="0 6 * * *" \
     --active=1

Schedule an immediate run:

.. code-block:: bash

   multiflexi-cli run-template:schedule --id=158 --schedule_time=now

When ``--executor`` is omitted on ``schedule``, the executor stored on the
runtemplate is used.

You can also select **Kubernetes** in the web UI when editing a runtemplate.

Execution flow
--------------

When the daemon picks up a job with the Kubernetes executor:

1. **Helm status** (only if ``helmchart`` is set) — ``helm status <release>``
2. **Helm pre-deploy** (if needed) — ``helm upgrade --install`` with
   ``--create-namespace``, ``--wait``, and the configured timeout
3. **Path remap** — host ``MULTIFLEXI_TMP`` (and env values under that
   directory) are rewritten to ``/tmp`` inside the pod; originals are restored
   after collection so ``Job::runEnd()`` sees host paths
4. **Pod create** — without artifacts: ``kubectl run --restart=Never --attach
   --rm``; with artifacts from application.json ``artifacts`` /
   ``app_artifacts``: create the pod without attach, run the command, write an
   exit marker, then ``sleep`` so the pod stays ``Running`` long enough for
   ``kubectl cp``
5. **Output capture** — attach streams stdout/stderr directly; artifact mode
   uses ``kubectl logs`` after the exit marker appears. Helper commands (Helm,
   ``kubectl cp``, delete) use a quiet runner and do not overwrite job output
6. **Artifacts** — list pod ``/tmp``, match every ``app_artifacts.path``
   pattern (same regex rules as ``Application::getResultFiles()``),
   ``kubectl cp`` into host ``MULTIFLEXI_TMP``; ``Job::runEnd()`` then stores
   them in the ``artifacts`` table
7. **Cleanup** — delete the pod unless ``keepPodOnFailure`` is true and the
   job failed; without artifacts, ``kubectl run --rm`` removes the pod
8. **Persist** — stdout, stderr, exit code, and command line on the job row

Namespace resolution order: ``MULTIFLEXI_K8S_NAMESPACE`` → Helm namespace
(default ``multiflexi`` when a chart is configured) → cluster default.

Verification
------------

Packages and files on the host:

.. code-block:: bash

   dpkg -l multiflexi-executor multiflexi-executor-k8s
   sudo grep -E '^(KUBECONFIG|MULTIFLEXI_K8S_NAMESPACE)=' /etc/multiflexi/multiflexi.env
   sudo ls -la /var/lib/multiflexi/.kube/config
   systemctl is-active multiflexi-executor

Cluster access as the daemon user:

.. code-block:: bash

   sudo -u multiflexi \
     KUBECONFIG=/var/lib/multiflexi/.kube/config \
     kubectl get pods -n multiflexi

   sudo -u multiflexi \
     KUBECONFIG=/var/lib/multiflexi/.kube/config \
     helm -n multiflexi list

After a scheduled job:

.. code-block:: bash

   multiflexi-cli job:get --id=<JOB_ID> --format=json

Check:

- ``executor`` is ``Kubernetes``
- ``exitcode`` is ``0`` on success
- ``stdout`` contains pod output
- ``command`` shows the ``kubectl run`` line

Troubleshooting
---------------

Permission denied / Forbidden
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Confirm RBAC was applied in the same namespace you use in
  ``MULTIFLEXI_K8S_NAMESPACE``.
- Confirm the kubeconfig user is SA ``multiflexi-executor``, not an unrelated
  account.
- ``kubectl get namespace multiflexi`` may return Forbidden for the SA (the
  Role is namespaced and does not grant Namespace get). Listing pods in that
  namespace is the right smoke test.

Helm pre-deployment fails
~~~~~~~~~~~~~~~~~~~~~~~~~

- **"path not found"** — ``helmchart`` is not readable by ``multiflexi``.
- **OCI 404/403** — chart missing or needs ``helm registry login`` as
  ``multiflexi``.
- **"cluster unreachable"** — missing kubeconfig, wrong mode/owner, or wrong
  ``KUBECONFIG`` in ``multiflexi.env``.

ImagePullBackOff
~~~~~~~~~~~~~~~~

Fix the image tag or registry credentials used by the chart / ``ociimage``.

Empty stdout
~~~~~~~~~~~~

1. Confirm the app writes to stdout (not only to files).
2. Inspect job ``stderr``.
3. Ensure you run a Kubernetes executor build that preserves job stdout across
   helper ``kubectl``/``helm`` calls (``jobStdout`` / ``jobStderr`` fields).

Executor not recognized (falls back to Native)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``multiflexi-cli run-template:get --id=<ID> --format=json`` — ``executor``
  must be ``Kubernetes``
- ``/usr/share/php/MultiFlexi/Executor/Kubernetes.php`` must exist (package
  ``multiflexi-executor-k8s``)
- ``sudo systemctl restart multiflexi-executor``

Token expired
~~~~~~~~~~~~~

Regenerate the SA token (step 5), reinstall the kubeconfig (step 6), and
restart the daemon (step 8).
