.. _credential-prototype:

Credential Prototype Development
=================================

Credential prototypes define reusable sets of configuration fields that applications can reference. They describe *what credentials look like* (e.g. "Fio Bank API token + account number") without storing actual secret values. Applications declare which credential prototype they need, and administrators fill in the real values per company.

Schema Reference
----------------

MultiFlexi uses **JSON Schema version 0.2.0** to validate credential prototype definitions.

**Schema Location:**

.. code-block:: text

    https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/schema/credential-prototype.json

**Required Fields:**

- ``uuid``: Unique identifier (UUID v4 format)
- ``code``: Short alphanumeric identifier (2–64 chars, ``^[a-zA-Z0-9_-]+$``)
- ``name``: Human-readable name (string or localized object)
- ``version``: Semantic version (e.g. ``1.0.0``)

**Optional Fields:**

- ``description``: Description (string or localized object)
- ``homepage``: Project homepage URL
- ``tags``: Array of keyword strings for filtering and discovery
- ``url``: Additional information URL
- ``logo``: Filename of the SVG logo (stored in ``/usr/share/multiflexi/images/``)
- ``fields``: Array of field definitions (see below)

Field Definitions
-----------------

Each entry in the ``fields`` array describes one configuration field the credential type provides.

**Required field properties:**

- ``keyword``: Environment variable name (uppercase, ``^[A-Z][A-Z0-9_]*$``)
- ``type``: One of ``string``, ``password``, ``email``, ``url``, ``integer``, ``boolean``, ``select``, ``textarea``, ``file``

**Optional field properties:**

- ``name``: Human-readable label (string or localized object)
- ``description``: Field description (string or localized object)
- ``hint``: Placeholder text shown in the form input
- ``default_value``: Pre-filled default value
- ``required``: Boolean, whether the field must be filled (default: ``false``)
- ``options``: Array of ``{"value": "...", "label": "..."}`` objects (for ``select`` type)

Localization
------------

The ``name`` and ``description`` fields at both the prototype and field level support localization. Use either a plain string or an object with ISO 639-1 language codes as keys:

.. code-block:: json

    {
        "name": {
            "en": "Fio Bank",
            "cs": "Fio Banka"
        },
        "description": {
            "en": "Credential type for Fio Bank API integration",
            "cs": "Typ přihlašovacích údajů pro integraci s Fio Bank API"
        }
    }

When a localized object is used, the English (``en``) value is stored as the default in the database. All language variants are stored in the ``credential_prototype_translations`` and ``credential_prototype_field_translations`` tables.

Minimal Example
---------------

.. code-block:: json

    {
        "$schema": "https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/schema/credential-prototype.json",
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "code": "MyService",
        "name": "My Service API",
        "description": "Credentials for My Service REST API",
        "version": "1.0.0",
        "homepage": "https://github.com/example/my-service",
        "tags": ["API", "REST", "my-service"],
        "logo": "my-service.svg",
        "fields": [
            {
                "keyword": "MY_SERVICE_URL",
                "type": "url",
                "name": "API Endpoint",
                "description": "Base URL of the My Service API",
                "hint": "https://api.my-service.com/v1",
                "required": true
            },
            {
                "keyword": "MY_SERVICE_TOKEN",
                "type": "password",
                "name": "API Token",
                "description": "Authentication token for the API",
                "required": true
            }
        ]
    }

Full Example with Localization
------------------------------

.. code-block:: json

    {
        "$schema": "https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/schema/credential-prototype.json",
        "uuid": "f79aaa38-2eaf-453a-beee-3a2afa1221d5",
        "code": "FioBank",
        "name": {
            "en": "Fio Bank",
            "cs": "Fio Banka"
        },
        "description": {
            "en": "Fio Bank credential type for integration with Fio Bank API",
            "cs": "Typ přihlašovacích údajů pro integraci s Fio Bank API"
        },
        "version": "1.0",
        "logo": "Fio.svg",
        "homepage": "https://www.fio.cz/",
        "tags": ["Fio", "bank", "finance", "API"],
        "fields": [
            {
                "keyword": "ACCOUNT_NUMBER",
                "type": "string",
                "name": {
                    "en": "Fio Bank Account Number",
                    "cs": "Číslo účtu Fio Banky"
                },
                "description": {
                    "en": "Number of the Fio Bank account",
                    "cs": "Číslo účtu ve Fio Bance"
                },
                "hint": "123456789/2010",
                "required": false
            },
            {
                "keyword": "FIO_TOKEN",
                "type": "string",
                "name": {
                    "en": "Fio Bank Token",
                    "cs": "Token Fio Banky"
                },
                "description": {
                    "en": "Token for accessing the Fio Bank API",
                    "cs": "Token pro přístup k Fio Bank API"
                },
                "required": true
            }
        ]
    }

File Naming Convention
----------------------

Credential prototype JSON files follow the naming pattern:

.. code-block:: text

    <lowercase-code>.credprototype.json

For example: ``fiobank.credprototype.json``, ``mail.credprototype.json``.

Place the file in the ``multiflexi/`` directory of your project:

.. code-block:: text

    my-project/
    ├── multiflexi/
    │   ├── my-app.multiflexi.app.json
    │   ├── my-service.credprototype.json
    │   └── my-service-logo.svg
    ├── src/
    └── debian/

Logo Files
----------

Logo SVGs are shared across all MultiFlexi web frontends (multiflexi.eu, multiflexi-web5, multiflexi-web). They are served from a unified location:

**Development:** ``src/images/{uuid}.svg`` or ``src/images/{LogoFilename}``

**Production (Debian):** ``/usr/share/multiflexi/images/``

In your ``debian/*.install`` file, install the logo to the shared path:

.. code-block:: text

    multiflexi/*.svg   usr/share/multiflexi/images/

.. warning::

    Do **not** install logos to ``/usr/share/multiflexi-web/images/`` — that path is reserved for web UI assets. All application and credential prototype logos go to ``/usr/share/multiflexi/images/``.

Database Schema
---------------

The credential prototype data is stored across four tables:

**credential_prototype** — main prototype record:

- ``id``, ``uuid``, ``code``, ``name``, ``description``, ``version``
- ``url``, ``homepage``, ``tags``, ``logo``
- ``created_at``, ``updated_at``

**credential_prototype_field** — field definitions per prototype:

- ``credential_prototype_id``, ``keyword``, ``type``, ``name``, ``description``
- ``hint``, ``default_value``, ``required``, ``options`` (JSON)

**credential_prototype_translations** — localized name/description per language:

- ``credential_prototype_id``, ``lang``, ``name``, ``description``

**credential_prototype_field_translations** — localized field strings per language:

- ``credential_prototype_field_id``, ``lang``, ``name``, ``description``, ``hint``

CLI Commands
------------

**Sync** credential prototype JSON files from installed packages into the database:

.. code-block:: bash

    sudo multiflexi credential-prototype:sync

This scans all ``*.credprototype.json`` files from installed package paths (``/usr/lib/*/multiflexi/``) and imports or updates them in the database. Run it after installing or upgrading packages that ship credential prototype definitions.

**List** all registered credential prototypes:

.. code-block:: bash

    sudo multiflexi credential-prototype:list

Import and Export
-----------------

**Programmatic import** (PHP):

.. code-block:: php

    $prototype = new \MultiFlexi\CredentialProtoType();
    $jsonData = json_decode(file_get_contents('myservice.credprototype.json'), true);
    $prototype->importJson($jsonData);

**Programmatic export** (PHP):

.. code-block:: php

    $prototype = new \MultiFlexi\CredentialProtoType(42);  // load by ID
    $exported = $prototype->exportJson();
    file_put_contents('export.json', json_encode($exported, JSON_PRETTY_PRINT));

The ``exportJson()`` method outputs localized fields as objects when translations exist, and includes ``homepage`` and ``tags`` when populated.

PHP Credential Prototype Classes
---------------------------------

In addition to JSON definitions, credential prototypes can be implemented as PHP classes extending ``\MultiFlexi\CredentialProtoType``. This is useful when the credential type needs runtime logic (e.g. reading a ``.env`` file, querying a vault, or validating connections).

.. code-block:: php

    namespace MultiFlexi\CredentialProtoType;

    class MyService extends \MultiFlexi\CredentialProtoType
        implements \MultiFlexi\credentialTypeInterface
    {
        public static string $logo = 'my-service.svg';

        public function __construct()
        {
            parent::__construct();

            $apiUrl = new \MultiFlexi\ConfigField(
                'MY_SERVICE_URL', 'url',
                _('API Endpoint'), _('Base URL of the My Service API')
            );
            $apiUrl->setHint('https://api.example.com')->setRequired(true);

            $token = new \MultiFlexi\ConfigField(
                'MY_SERVICE_TOKEN', 'password',
                _('API Token'), _('Authentication token')
            );
            $token->setRequired(true);

            $this->configFieldsInternal->addField($apiUrl);
            $this->configFieldsInternal->addField($token);
        }

        public function uuid(): string
        {
            return '550e8400-e29b-41d4-a716-446655440000';
        }

        public function name(): string
        {
            return _('My Service API');
        }

        public function description(): string
        {
            return _('Credentials for My Service REST API');
        }

        public function logo(): string
        {
            return self::$logo;
        }
    }

Even when using a PHP class, it is recommended to also ship a ``.credprototype.json`` file so the ``credential-prototype:sync`` CLI command can register the prototype's ``homepage``, ``tags``, and localized strings.

Packaging Checklist
-------------------

When creating a Debian package that includes a credential prototype:

1. Place the JSON definition in ``multiflexi/<code>.credprototype.json``
2. Place the logo SVG in ``multiflexi/<code>.svg`` or ``src/images/<LogoName>.svg``
3. Add to ``debian/<package>.install``:

   .. code-block:: text

       multiflexi/*.json   usr/lib/<package>/multiflexi/
       multiflexi/*.svg    usr/share/multiflexi/images/

4. The ``postinst`` script should call ``multiflexi credential-prototype:sync`` to register the prototype in the database after package installation.

5. Include ``homepage`` and ``tags`` fields in the JSON for discoverability on `multiflexi.eu <https://multiflexi.eu/>`_.
