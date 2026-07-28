SBOM Process
============

This page is the single source of truth for how Software Bills of Material
(SBOMs) are generated across the MultiFlexi ecosystem, which format is used,
and which repositories currently have coverage.

An SBOM is a machine-readable inventory of a piece of software's
dependencies. It is a prerequisite for reasoning about supply-chain risk and
for any EU Cyber Resilience Act (CRA) compliance path — see
:doc:`cra-scope-notes` for how this fits into CRA readiness. Producing SBOMs
is good practice independent of CRA scope.

Format and tooling
-------------------

MultiFlexi repositories span five dependency ecosystems. `CycloneDX
<https://cyclonedx.org/>`_ was chosen over SPDX because it has a mature,
actively maintained generator for every ecosystem present in the org, and
because PHP/Composer — the dominant ecosystem across MultiFlexi repos — is
best served by CycloneDX's own reference implementation
(``cyclonedx-php-composer``). All generators below were installed and
validated (2026-07) against a representative repo per ecosystem before
being adopted.

.. list-table::
   :header-rows: 1
   :widths: 18 42 40

   * - Ecosystem
     - Tool
     - Notes
   * - PHP / Composer
     - ``cyclonedx/cyclonedx-php-composer``
     - Composer plugin. Requires a ``composer.lock`` **on disk** — it cannot
       generate from ``composer.json`` version ranges alone. Installed in an
       isolated ``COMPOSER_HOME`` so it never touches a project's own
       ``composer.json``/``composer.lock``.
   * - Python
     - ``cyclonedx-bom`` (CLI: ``cyclonedx-py``)
     - Used against ``requirements.txt``. Repos with only ``pyproject.toml``
       (no ``requirements.txt``) are currently **not** covered — the CLI has
       no direct PEP 621 support, only ``poetry``/``pipenv``/``conda``/
       ``environment`` subcommands.
   * - npm / Node
     - ``@cyclonedx/cyclonedx-npm``
     - Requires a committed ``package-lock.json`` (or an installed
       ``node_modules``) — unlike the Python tool, it will not approximate
       from ``package.json`` alone.
   * - Go
     - ``cyclonedx-gomod``
     - Reads ``go.mod``/``go.sum`` directly, no separate lockfile concept.
   * - Java / Maven
     - ``cyclonedx-maven-plugin``
     - Invoked via ``mvn ... makeAggregateBom``, no separate install beyond
       Maven itself.

Output format is CycloneDX JSON (schema 1.5/1.6, whichever the installed
generator emits). One file per repo per matched ecosystem (a repo can match
more than one, e.g. a PHP repo with an npm-based frontend produces two
files).

How to regenerate
------------------

The generation scripts live in a local tooling directory (not yet published
as its own repository — see the audit note below) and follow the naming
convention ``<repo>.<ecosystem>.cdx.json``:

.. code-block:: bash

   # Single repo
   ./generate-sbom.sh /path/to/repo [output-dir]

   # All in-scope repos under a workspace root
   ./generate-sbom-all.sh [workspace-root] [output-dir]

Both scripts are idempotent: output paths are deterministic and always
overwritten in place, never appended to or duplicated. If a required
generator isn't installed, or a repo is missing the lockfile its generator
needs, that ecosystem is skipped with a clear warning rather than failing
the whole batch — and the gap is recorded so it's visible rather than
silently dropped.

Current coverage vs. gaps
--------------------------

A full inventory (which repos have a lockfile, which already had SBOM/
scanning tooling before this audit, which now have a generated SBOM) is
maintained as a raw data artifact rather than duplicated here — see
``_audit/sbom-cra-audit-2026-07.md`` in the repository root for the full
tables. In summary, as of the 2026-07 audit:

- No repository in the MultiFlexi org had any SBOM or dependency-scanning
  tooling beyond GitHub Dependabot (enabled on 9 of the ~40 actively
  maintained repos).
- PHP/Composer is the dominant ecosystem (roughly 20 of the ~40 locally
  maintained repos), followed by Python, npm, Go, and Java.
- Several repos have a dependency manifest but no committed lockfile, which
  blocks accurate SBOM generation for those repos until a lockfile is
  generated and committed. These are listed explicitly in the audit
  artifact rather than silently skipped.
- Six Debian-packaging-only repos (no application-level dependency manifest)
  are out of scope for this pass. A Debian ``Build-Depends``-based SBOM is a
  distinct mechanism and is deferred to a future phase.

CI integration (proposed, not yet adopted)
--------------------------------------------

A draft GitHub Actions workflow template exists as a proposal
(``sbom-workflow.yml.example`` alongside the generation scripts) but is
**not** wired into any repository's actual CI. Adopting it in a given repo
is a separate, per-repo decision — CI changes are cross-cutting and are
intentionally out of scope for the audit itself. The repos already using
Dependabot are the suggested first candidates, since they already have
dependency-hygiene buy-in.
