.. _application-development:

Application Development Framework
=================================

This section provides comprehensive technical details for developing MultiFlexi applications.

Application Definition Schema
-----------------------------

MultiFlexi uses **JSON Schema version 3.0.0** to validate application definitions. The schema ensures correctness of structure, types, and constraints.

**Schema Location:**

.. code-block:: text

    https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/multiflexi.app.schema.json

**Schema Version:** 3.0.0

**Key Schema Features:**

- **Localized Strings**: Support for multi-language names, descriptions, and hints
- **Strict Field Validation**: Environment variable names must match ``^[A-Z0-9_]+$``
- **Type Safety**: Environment variable types are strictly validated
- **UUID Format**: Application UUIDs must conform to UUID v4 format
- **URI Validation**: Homepage and schema references validated as URIs
- **OCI Image Pattern**: Docker/OCI images validated with regex pattern
- **Category Enums**: Environment categories limited to: API, Database, Behavior, Security, Other
- **Data Flow**: ``produces`` and ``consumes`` sections for input/output declaration

**Required Fields:**

- ``$schema``: Must reference the official schema URL
- ``name``: Application name (string or localized object)
- ``description``: Application description (string or localized object)
- ``executable``: Command to execute
- ``environment``: Environment variables object (can be empty ``{}``)

**Validation Command:**

.. code-block:: bash

    multiflexi-cli application validate-json --json /path/to/app.json

**Common Validation Errors:**

1. **Missing ``$schema`` field**: Always include the schema reference at the top of your JSON
2. **Invalid environment variable names**: Must be uppercase with underscores (``MY_VAR``, not ``myVar``)
3. **Wrong type enum**: Use exact values from schema (``file-path``, not ``filepath``)
4. **Invalid UUID format**: Use proper UUID v4 format (e.g., ``550e8400-e29b-41d4-a716-446655440000``)
5. **Invalid category**: Use only: API, Database, Behavior, Security, Other
6. **Localized string format**: Must be either string OR object with language codes

**Migration from Older Schemas:**

If you have older application definitions:

- Add ``$schema`` field at the top
- Change ``topics`` string to ``tags`` array: ``"topics": "A,B,C"`` → ``"tags": ["A", "B", "C"]``
- Change ``cmdparams`` to ``cmdparamsTemplate`` with ``${VAR}`` syntax instead of ``{VAR}``
- Remove deprecated fields: ``setup``, ``deploy``, ``requirements``, ``multiflexi``
- Add ``schemaVersion": "3.0.0"`` to explicitly declare compatibility

Advanced Application Examples
-----------------------------

**Basic Example:**

Here is a simple example conforming to schema version 3.0.0:

.. code-block:: json

  {
      "$schema": "https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/multiflexi.app.schema.json",
      "name": "RB transaction report",
      "description": "Raiffeisenbank transaction report",
      "executable": "raiffeisenbank-transaction-report",
      "uuid": "97f30cf9-2d9e-4d91-ad65-9bdd8b4663cd",
      "version": "1.0.0",
      "author": "Spoje.Net",
      "license": "MIT",
      "homepage": "https://github.com/Spoje-NET/raiffeisenbank-statement-tools",
      "ociimage": "docker.io/spojenet/raiffeisenbank-statement-tools:latest",
      "category": "Banking",
      "tags": ["Bank", "RaiffeisenBank", "Transactions", "Report"],
      "environment": {
          "ACCOUNT_NUMBER": {
              "type": "string",
              "category": "API",
              "description": "Bank Account Number",
              "required": true
          },
          "CERT_PASS": {
              "type": "password",
              "category": "Security",
              "description": "Certificate Password",
              "required": true
          }
      }
  }

**Advanced Example with Localization, Artifacts, and Data Flow:**

.. code-block:: json

  {
      "$schema": "https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/multiflexi.app.schema.json",
      "schemaVersion": "3.0.0",
      "name": {
          "en": "Invoice Processor",
          "cs": "Zpracovatel faktur",
          "de": "Rechnungsverarbeiter"
      },
      "description": {
          "en": "Processes invoices and generates reports",
          "cs": "Zpracovává faktury a generuje reporty",
          "de": "Verarbeitet Rechnungen und erstellt Berichte"
      },
      "executable": "invoice-processor",
      "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "version": "2.1.0",
      "author": "Your Company",
      "license": "GPL-3.0",
      "category": "Accounting",
      "tags": ["Invoice", "Accounting", "Report", "PDF"],
      "cmdparamsTemplate": "--config ${CONFIG_FILE} --output ${OUTPUT_DIR}",
      "environment": {
          "CONFIG_FILE": {
              "type": "file-path",
              "category": "Behavior",
              "description": {
                  "en": "Path to configuration file",
                  "cs": "Cesta ke konfiguračnímu souboru"
              },
              "hint": {
                  "en": "Use absolute path or relative to working directory",
                  "cs": "Použijte absolutní cestu nebo relativní k pracovnímu adresáři"
              },
              "defval": "/etc/invoice-processor/config.yaml",
              "required": false
          },
          "OUTPUT_DIR": {
              "type": "file-path",
              "category": "Behavior",
              "description": "Output directory for generated files",
              "defval": "/tmp/invoices",
              "required": true
          },
          "DB_CONNECTION": {
              "type": "string",
              "category": "Database",
              "description": "Database connection string",
              "required": true
          },
          "LOG_LEVEL": {
              "type": "set",
              "category": "Behavior",
              "description": "Logging verbosity level",
              "defval": "info",
              "options": ["debug", "info", "warning", "error"],
              "required": false
          }
      },
      "artifacts": [
          {
              "name": "invoice-report",
              "path": "${OUTPUT_DIR}/invoice-report.pdf",
              "type": "application/pdf",
              "description": "Generated invoice report in PDF format"
          },
          {
              "name": "metrics",
              "path": "${OUTPUT_DIR}/metrics.json",
              "type": "application/json",
              "description": {
                  "en": "Processing metrics and statistics",
                  "cs": "Metriky a statistiky zpracování"
              }
          }
      ],
      "produces": {
          "invoice-data": {
              "description": "Processed invoice data in JSON format",
              "format": "json",
              "patterns": ["${OUTPUT_DIR}/*.json"]
          },
          "reports": {
              "description": "PDF reports",
              "format": "file",
              "patterns": ["${OUTPUT_DIR}/*.pdf"]
          }
      },
      "consumes": {
          "raw-invoices": {
              "description": "Raw invoice files to process",
              "required": true,
              "format": "file"
          }
      }
  }

Report JSON Schema for Developers
----------------------------------

Applications can optionally emit structured execution reports consumed by MultiFlexi (and e.g. exported to monitoring/analysis systems). These reports are validated by a separate JSON Schema.

Purpose:

* Provide a consistent machine-readable structure for application output summaries
* Allow validation before ingestion (fail fast on malformed data)
* Enable tooling (dashboards, exporters) to rely on stable field names

Key Concepts (as defined in the report schema):

* Metadata about the producing application (UUID, name, version)
* Timing information (start/end timestamps, duration)
* Result classification (status / severity / exit code)
* Produced artifacts (paths, checksums, sizes) when relevant
* Metrics (numeric values with units or context)
* Messages / log excerpts (structured list)
* Optional links (URLs to external resources or dashboards)

Validation Schema:

`multiflexi.report.schema.json <https://github.com/VitexSoftware/php-vitexsoftware-multiflexi-core/blob/main/multiflexi.report.schema.json>`_

Basic Report Example:

.. code-block:: json

   {
     "app_uuid": "97f30cf9-2d9e-4d91-ad65-9bdd8b4663cd",
     "app_name": "RB transaction report",
     "generated_at": "2025-09-24T12:34:56Z",
     "status": "success",
     "duration_ms": 8421,
     "metrics": [
       { "name": "transactions_processed", "value": 128, "unit": "count" },
       { "name": "total_amount", "value": 51234.77, "unit": "CZK" }
     ],
     "artifacts": [
       { "path": "output/report-2025-09-24.json", "size": 20480 }
     ],
     "messages": [
       { "level": "info", "text": "Processing completed" }
     ]
   }

Implementation Notes:

* If your application already writes a domain-specific JSON output, you can wrap or transform it into the report schema just before exit.
* Keep timestamps in ISO 8601 (UTC) for portability.
* Use stable metric names—prefer lowercase with underscores.
* Omit sections (e.g. artifacts, metrics) rather than sending empty arrays if not applicable (schema usually allows absence).
* Validate locally during development with any JSON Schema validator before integrating.

Application Development Examples
--------------------------------

Examples for App developers can be found at:

- `MultiFlexi-Python-App-example <https://github.com/VitexSoftware/MultiFlexi-Python-App-example>`_
- `MultiFlexi-Java-App-Example <https://github.com/VitexSoftware/MultiFlexi-Java-App-Example>`_
- `MultiFlexi-Rust-App-Example <https://github.com/VitexSoftware/MultiFlexi-Rust-App-Example>`_

Examples for other languages coming soon.

