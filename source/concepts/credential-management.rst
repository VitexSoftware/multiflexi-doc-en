Credential Management
=====================

**Target Audience:** Users, Administrators
**Difficulty:** Intermediate
**Prerequisites:** Understanding of :doc:`data-model`

.. contents::
   :local:
   :depth: 2

Overview
--------

MultiFlexi uses a **three-tier credential architecture** that separates the *definition* of a credential type from its *configuration* at the company level, and from its *actual use* within individual jobs.

.. code-block:: text

    CredentialPrototype  ──►  CredentialType  ──►  Credential
    (JSON template /           (company-level        (assigned to
     system definition)         instance with         a RunTemplate)
                                actual values)

This design allows the same credential type (e.g. "AbraFlexi ERP connection") to be defined once and then configured separately for each company that uses it, with full isolation between companies.

Tier 1: CredentialPrototype
----------------------------

A **CredentialPrototype** is a JSON-based template that describes a category of credentials: what fields it requires, their types and validation rules, and how it should be presented in the UI.

Prototypes are shipped as Debian packages (e.g. ``multiflexi-abraflexi``, ``multiflexi-mail``, ``multiflexi-vaultwarden``) or imported manually via the CLI.

**Standard credential prototype packages:**

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Package
     - Description
   * - ``multiflexi-abraflexi``
     - AbraFlexi ERP connection
   * - ``multiflexi-csas``
     - Česká Spořitelna / ČSAS / Erste API
   * - ``multiflexi-raiffeisenbank``
     - Raiffeisenbank Premium API
   * - ``multiflexi-mail``
     - SMTP / e-mail (Symfony Mailer)
   * - ``multiflexi-database-connection``
     - PDO database connection
   * - ``multiflexi-vaultwarden``
     - VaultWarden / Bitwarden secrets
   * - ``multiflexi-mtr``
     - MTR network diagnostics

**Installing a prototype package:**

.. code-block:: bash

   sudo apt install multiflexi-abraflexi

After installation, the prototype is automatically registered in MultiFlexi.

**Importing a custom prototype from JSON:**

.. code-block:: bash

   multiflexi-cli crprototype import --file my-integration.json

**Listing registered prototypes:**

.. code-block:: bash

   multiflexi-cli crprototype list

Prototype JSON Schema
~~~~~~~~~~~~~~~~~~~~~

All prototype JSON files must conform to the credential type schema. The schema enforces:

- ``code``: 2–64 alphanumeric characters (unique identifier)
- ``name``, ``description``, ``version``, ``logo``, ``url``
- ``fields``: array of field definitions with types and validation rules

**Supported field types:** ``string``, ``password``, ``url``, ``email``, ``integer``, ``boolean``, ``select``

**Example prototype JSON:**

.. code-block:: json

   {
     "code": "MYERP",
     "name": "My ERP Connection",
     "description": "Credentials for My ERP REST API",
     "version": "1.0.0",
     "fields": [
       {
         "code": "MYERP_URL",
         "name": "Server URL",
         "type": "url",
         "required": true
       },
       {
         "code": "MYERP_USER",
         "name": "Username",
         "type": "string",
         "required": true
       },
       {
         "code": "MYERP_PASSWORD",
         "name": "Password",
         "type": "password",
         "required": true
       }
     ]
   }

Tier 2: CredentialType
-----------------------

A **CredentialType** is a company-level *instance* of a CredentialPrototype. When a company needs to use a particular integration, an administrator creates a CredentialType for that company, filling in the actual connection values (URL, username, password, API key, etc.).

A single prototype can have multiple CredentialType instances per company — for example, a company may have separate AbraFlexi connections for production and staging environments.

**Creating a CredentialType via the web interface:**

1. Navigate to **Companies** → select your company → **Credentials**
2. Click **"+ Add Credential Type"**
3. Select the desired **Prototype** from the dropdown
4. Fill in the connection values (URL, API key, etc.)
5. Optionally give it a descriptive **Label** (e.g. "Production AbraFlexi")
6. Click **Save**

**Creating a CredentialType via CLI:**

.. code-block:: bash

   multiflexi-cli credential-type:create \
     --company=1 \
     --prototype=ABRAFLEXI \
     --label="Production AbraFlexi" \
     --ABRAFLEXI_URL=https://erp.example.com \
     --ABRAFLEXI_USER=admin \
     --ABRAFLEXI_PASSWORD=secret

**Listing CredentialTypes for a company:**

.. code-block:: bash

   multiflexi-cli credential-type:list --company=1

Tier 3: Credential (Assignment)
---------------------------------

A **Credential** is the assignment of a CredentialType to a specific RunTemplate. This is what actually injects the credential environment variables into the job when it runs.

One RunTemplate can have multiple credentials assigned — for example, a job that reads from AbraFlexi and sends email needs both an AbraFlexi CredentialType and a Mail CredentialType.

**Assigning a credential via the web interface:**

1. Open the RunTemplate detail page
2. Click **"Credentials"** tab
3. Click **"+ Assign Credential"**
4. Select the CredentialType from the list
5. Save

See :doc:`../howto/assigning-credentials` for a detailed step-by-step guide.

**Assigning a credential via CLI:**

.. code-block:: bash

   multiflexi-cli run-template:assign-credential \
     --runtemplate=42 \
     --credentialtype=7

Configuration Cleanup on Assignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An assigned credential provides its own set of configuration fields. If the
RunTemplate already stores a configuration value under the same name as one of
those provided fields, the stored value would be silently overwritten while the
job environment is assembled.

To keep the configuration unambiguous, MultiFlexi removes every stored
RunTemplate configuration field whose name matches a field provided by the newly
assigned credential. Each removed value is written to the log, so the change is
auditable.

Only the RunTemplate's own stored values are removed. The credential keeps
providing the field, so the effective job environment is unchanged apart from the
now-redundant duplicate entry.

How Credentials Are Injected into Jobs
----------------------------------------

When a job runs, MultiFlexi merges all assigned CredentialType fields into the job's environment. Field codes become environment variable names.

For example, if a CredentialType has a field ``ABRAFLEXI_URL`` with value ``https://erp.example.com``, the job process will have:

.. code-block:: bash

   ABRAFLEXI_URL=https://erp.example.com

This means any application that respects these environment variables will automatically connect to the correct endpoint for the correct company — without storing credentials in the application itself.

Security Considerations
------------------------

- Fields marked ``"type": "password"`` or ``"type": "secret"`` in a prototype
  definition (or with an explicit ``"secret": true`` flag) are treated as
  **redactable**: MultiFlexi never returns their real value through the web
  UI, the REST API, or the CLI's default output. Instead they show a fixed
  placeholder — ``••••••••`` when a value is stored, ``(not set)`` when it
  isn't. The placeholder length never varies with the secret's length, since
  that itself would leak information.
- Credential values are encrypted at rest (AES-256-GCM) in the database when
  ``DATA_ENCRYPTION_ENABLED=true`` (the default) and
  ``multiflexi-cli encryption:init`` has been run. Encryption keys are
  versioned: rotating a key (``encryption:init --force``) keeps the previous
  version's key material so data encrypted under it stays decryptable — it
  does not invalidate existing credentials. See
  :doc:`../reference/configuration` for the relevant environment variables
  and :ref:`cli-encryption-commands` for key lifecycle commands.
- Editing a credential never re-displays its stored secret value. Changing
  it always means entering a new value; leaving the field blank keeps the
  existing value unchanged. This applies uniformly to the web form, the
  REST API, and the CLI.
- The **only** way to see a stored secret's real value is
  ``multiflexi-cli credential:get --reveal``, which prompts for confirmation
  and writes an audit log entry (event ``credential_revealed``) each time it
  is used. No such path exists in the REST API or the web UI — job execution
  itself resolves credentials in-process and never needs to go through
  these redacted, human-facing surfaces.
- Credentials are company-scoped: users can only see credentials for their
  assigned company.
- VaultWarden integration (``multiflexi-vaultwarden``) can be used to store
  secrets externally instead of in the MultiFlexi database.

See Also
--------

- :doc:`data-model` — How credentials relate to other entities
- :doc:`../howto/assigning-credentials` — Practical step-by-step credential assignment
- :doc:`../reference/application-schema` — Application credential requirements
- :doc:`../reference/configuration` — Encryption settings
