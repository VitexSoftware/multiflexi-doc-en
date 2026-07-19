Platform Support Matrix
========================

This page is the single source of truth for which Debian and Ubuntu
releases MultiFlexi packages support, build for, and recommend. If any
other page states a different set of supported OS versions, this page
wins — please open an issue or fix the drift.

Regular support vs. LTS: what "EOL" headlines actually mean
-------------------------------------------------------------

Debian releases get **five years** of security coverage in two phases:

- **Regular support** (~3 years) — maintained by the Debian Security Team,
  full package coverage, all supported architectures.
- **Long Term Support / LTS** (following ~2 years) — maintained by the
  separate Debian LTS Team. Coverage narrows: only packages with an active
  LTS sponsor are covered, and the architecture list shrinks. LTS is
  **not** the same as end-of-life — the distribution keeps receiving
  security fixes, just with a smaller package/architecture scope.

Third-party blog posts and aggregator sites sometimes label the regular
support cutoff as "EOL," which overstates it — the release isn't
abandoned, it moves to LTS. Debian 12 (Bookworm) is a current example: its
regular support ended and LTS coverage began on **2026-07-12**; it remains
under active security maintenance until **2028-06-30**.

Support matrix
---------------

.. list-table::
   :header-rows: 1
   :widths: 18 16 14 16 36

   * - OS / Suite
     - Status
     - Coverage ends
     - Architecture
     - Notes
   * - Debian 13 (Trixie)
     - **Primary / recommended**
     - Regular support until ~2028, LTS until ~2030
     - amd64
     - Actively promoted in install docs, README, and all "get started"
       paths. Build target across all packages.
   * - Ubuntu 24.04 LTS (Noble Numbat)
     - Supported
     - Standard support to 2029, ESM to 2034
     - amd64
     - Fully supported alternative to Debian 13.
   * - Ubuntu 22.04 LTS (Jammy Jellyfish)
     - Supported
     - Standard support to 2027, ESM to 2032
     - amd64
     - Still built and published; not the primary recommendation for new
       installs.
   * - Debian 12 (Bookworm)
     - **Build maintained, no longer promoted**
     - LTS until 2028-06-30 (regular support ended 2026-07-12)
     - amd64
     - CI keeps building it as a canary so we know the package set still
       installs cleanly — it is intentionally **not** advertised as the
       recommended platform anywhere (README, install guide, marketing
       pages). Package-level LTS coverage for MultiFlexi's own dependency
       stack (PHP 8.2 runtime confirmed actively covered; MariaDB/
       PostgreSQL/dbconfig-common coverage not yet individually confirmed —
       see the audit). See :ref:`bookworm-canary` below for the proposed
       sunset date.
   * - Debian 11 (Bullseye)
     - Unsupported by MultiFlexi
     - Debian LTS ends 2026-08-31
     - —
     - No MultiFlexi package currently builds or publishes for Bullseye
       (confirmed by repo audit, 2026-07). Its LTS end date is listed here
       for completeness only — it is not a deadline that affects
       MultiFlexi, since nothing ships for it today.
   * - Debian 14 (Forky)
     - Not yet supported
     - Unstable/testing
     - —
     - Explicitly disabled in every build pipeline: the Debian package
       ecosystem MultiFlexi depends on (several ``php-*`` and
       ``phinx``-related packages) is not yet installable on Forky. Will be
       re-enabled once the dependency stack builds cleanly there.

.. _bookworm-canary:

Debian 12 (Bookworm): "keep building, stop promoting"
--------------------------------------------------------

Debian 12 is **not being dropped**. The distinction that matters:

- **What stays the same:** the Jenkins release pipeline keeps building and
  publishing ``debian:bookworm`` packages on every release, exactly as it
  does for Trixie/Jammy/Noble. This is a canary build — its purpose is to
  catch the moment the package set stops installing cleanly on Bookworm,
  not to serve production traffic.
- **What changes:** Bookworm no longer appears as the recommended or
  default option anywhere user-facing — install instructions, README
  badges, quickstart prerequisites, or marketing pages. Debian 13 (Trixie)
  is what we tell people to install.
- **Proposed internal sunset date:** **mid-2027** — roughly a year before
  Bookworm's LTS window closes (2028-06-30). This is a *proposal*, not a
  committed decision; confirm with the maintainers before treating it as a
  deadline. Once confirmed, the canary build can be removed from the
  release pipelines at that point without waiting for the LTS end date
  itself.
- Full package-level coverage detail (what's confirmed vs. still needs
  checking against the Debian LTS tracker) is in the audit artifact:
  `_audit/debian-support-audit-2026-07.md
  <https://github.com/VitexSoftware/multiflexi-doc-en/blob/main/_audit/debian-support-audit-2026-07.md>`_.

Test repository scope is unchanged
-------------------------------------

The above narrowing (build-but-don't-promote for Bookworm, no Bullseye/
Forky) applies only to the **production** package repository
(``repo.vitexsoftware.com`` / ``repo.multiflexi.eu``). The **test
repository** (``repo.vitexsoftware.com`` staging scope used for pre-release
validation) keeps its current package scope unchanged — nothing here
proposes removing or scoping down anything published there.

Known inconsistencies (follow-up, not fixed by this doc)
------------------------------------------------------------

The repo audit (2026-07) surfaced a few places where CI configuration and
this documentation don't line up yet. These are flagged for the packaging
team, not resolved here:

- ``ubuntu:resolute`` (Ubuntu 25.10) has been added to 9 of roughly 30
  packaging pipelines but not the rest — an in-progress, inconsistent
  rollout. Not listed as a supported target above until it's uniform and a
  decision is made on whether to track a non-LTS Ubuntu release at all.
- ``multiflexi.eu``'s CI validation build (``debian/Jenkinsfile``) doesn't
  build for ``jammy`` even though its release pipeline
  (``debian/Jenkinsfile.release``) publishes for it.
- ``python3-multiflexi`` and ``node-red-contrib-multiflexi`` build for
  Trixie only (no Bookworm build at all) — narrower than the rest of the
  fleet.
- ``multiflexi-server``'s ``debian/Jenkinsfile`` and
  ``debian/Jenkinsfile.release`` no longer build for ``ubuntu:jammy``
  (removed 2026-07-19). ``php-slim-psr7`` isn't published for jammy in
  either Ubuntu's own universe archive or ``repo.vitexsoftware.com``, and
  jammy universe's own ``php-psr-http-factory`` is pinned at ``1.0.1-2``
  while ``php-slim-psr7`` requires ``>= 1.1`` — an unsatisfiable
  combination in the current jammy build image, not a MultiFlexi packaging
  bug. Effectively ``multiflexi-server`` is Trixie/Bookworm/Noble only
  until a compatible ``php-psr-http-factory`` (or ``php-slim-psr7``) build
  is available for jammy; the rest of the fleet still builds for jammy
  per the table above.

See the audit artifact for full detail.
