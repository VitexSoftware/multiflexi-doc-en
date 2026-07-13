# Debian/Ubuntu Support Matrix Audit — 2026-07

Raw findings behind `source/platform-support.rst`. Not part of the built
documentation; kept for traceability of the reasoning behind the support
matrix. Audited from local clones under `~/Projects/Multi/` on 2026-07-13.

## Method

- Searched every top-level VitexSoftware repo clone (excluding `vendor/`
  and `.claude/worktrees/` copies) for `debian/control`, `debian/Jenkinsfile`,
  `debian/Jenkinsfile.release`, `.github/workflows/*.yml`, and any
  reprepro/aptly `distributions` config.
- No `.github/workflows` files reference Debian/Ubuntu suite names — CI/CD
  for packaging runs entirely through Jenkins (`debian/Jenkinsfile` for
  per-commit build validation, `debian/Jenkinsfile.release` for the publish
  pipeline).
- No reprepro/aptly `distributions` file exists in any local clone; repo
  publishing config lives on the Jenkins/repo server itself, out of scope
  for a local audit.

## Task 1 — Packaging targets per repo

35 repos carry `debian/control` (i.e. build a `.deb`). Active (non-commented)
`distributions` arrays, read directly from each repo's
`debian/Jenkinsfile.release` (publish) and `debian/Jenkinsfile` (CI build):

| Repo | Jenkinsfile.release (publish) | Jenkinsfile (CI build) |
|---|---|---|
| multiflexi-abraflexi | bookworm, trixie, jammy, noble | same (comment-disabled forky) |
| multiflexi-all | bookworm, trixie, jammy, noble | same |
| multiflexi-api | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble |
| multiflexi-cli | bookworm, trixie, jammy, noble, **resolute** | bookworm, trixie, jammy, noble (forky disabled) |
| multiflexi-common | bookworm, trixie, jammy, noble, **resolute** | same |
| multiflexi-csas | bookworm, trixie, jammy, noble | same |
| multiflexi-database | bookworm, trixie, jammy, noble, **resolute** | same |
| multiflexi-database-connection | bookworm, trixie, jammy, noble | same |
| multiflexi-doc-en | bookworm, trixie, jammy, noble | same (forky disabled) |
| multiflexi.eu | bookworm, trixie, jammy, noble | bookworm, trixie, noble (jammy absent — inconsistency, flagged as follow-up) |
| multiflexi-event-processor | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble |
| multiflexi-executor | bookworm, trixie, jammy, noble | same |
| multiflexi-mail | bookworm, trixie, jammy, noble | same |
| multiflexi-microsoft365 | bookworm, trixie, jammy, noble (forky in comment only) | same |
| multiflexi-mserver | bookworm, trixie, jammy, noble | same |
| multiflexi-mtr | bookworm, trixie, jammy, noble | same |
| multiflexi-node-app | (no Jenkinsfile.release found) | forky present but disabled in comment; array not machine-parsed |
| multiflexi-probe | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble, **resolute** |
| multiflexi-raiffeisenbank | bookworm, trixie, jammy, noble, **resolute** | same |
| multiflexi-scheduler | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble |
| multiflexi-server | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble |
| multiflexi-tui | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble |
| multiflexi-vaultwarden | bookworm, trixie, jammy, noble | same |
| multiflexi-web | bookworm, trixie, jammy, noble, **resolute** | bookworm, trixie, jammy, noble, **resolute** |
| multiflexi-web5 | bookworm, trixie, jammy, noble, **resolute** | same |
| multiflexi-zabbix | bookworm, trixie, jammy, noble | bookworm, trixie, jammy, noble |
| multiflexi-zabbix-selenium | bookworm, trixie, jammy, noble | same |
| node-red-contrib-multiflexi | (no Jenkinsfile.release) | **trixie only** |
| php-vitexsoftware-multiflexi-core | bookworm, trixie, jammy, noble, **resolute** | same |
| python3-multiflexi | **trixie only** | trixie only |
| python3-shibuya-sphinx-theme | bookworm, trixie, jammy, noble, **resolute** | same (no Jenkinsfile.release array matched — verify) |
| repocompare | bookworm, trixie, jammy, noble | same |

Repos with `debian/control` but no matched Jenkinsfile suite array in this
pass (likely present but not parsed by the array-scan regex, or built via a
shared/templated Jenkinsfile): multiflexi-ansible-collection,
multiflexi-buildimages (builds the *build images themselves*, separate
concern), MultiFlexi-publish, jenkins-multiflexi (examples only).

### Key findings

1. **No repo currently builds or publishes for Debian 11 (Bullseye).** The
   only bullseye reference found anywhere in the workspace is inside a
   *vendored* third-party library snapshot
   (`multiflexi-web5/vendor/vitexsoftware/ease-html-widgets/debian/Jenkinsfile`),
   not a top-level MultiFlexi package's own pipeline. Bullseye LTS ends
   2026-08-31; since nothing ships for it today, this is a non-event for
   MultiFlexi, not a forcing deadline.
2. **Debian 14 (Forky) is explicitly disabled everywhere it appears**, with
   an inline comment consistent across repos: *"Forky is still
   unstable/research-only... full Debian package ecosystem is not yet
   available for Forky... re-enable once the stack builds cleanly."* This
   matches the recent `multiflexi-doc-en` commit
   `2f58df4 refactor(debian): remove unstable forky distribution from
   Jenkinsfile.release`. **`source/install.rst` still lists Debian 14
   (Forky) as supported — this is stale and is corrected in this pass.**
3. **`ubuntu:resolute` (Ubuntu 25.10) has been added to 9 of ~30 repos'
   publish pipelines** (multiflexi-cli, multiflexi-common,
   multiflexi-database, multiflexi-probe, multiflexi-raiffeisenbank,
   multiflexi-web, multiflexi-web5, php-vitexsoftware-multiflexi-core,
   python3-shibuya-sphinx-theme) but not the rest. This is an in-progress,
   inconsistent rollout — **flagged as a follow-up for the packaging team,
   not reflected as a supported target in the doc** since it isn't uniform
   yet and isn't an LTS release.
4. **python3-multiflexi and node-red-contrib-multiflexi build Trixie only**
   — narrower than the rest of the fleet (newer packages, no Bookworm
   build). Not a doc-blocking issue, just noted for completeness.
5. **multiflexi.eu's CI build Jenkinsfile omits `jammy`** while its release
   pipeline includes it — inconsistency between CI validation and what's
   actually published. Flagged as a follow-up, not fixed here (out of scope
   per task constraints: no CI config changes in this pass).
6. No suite-specific `.github/workflows` exist; all suite selection is
   Jenkins-driven. No local reprepro/aptly `distributions` file was found —
   repo publishing scope (production `repo.vitexsoftware.com` vs. the test
   repository) is server-side config not present in these clones, so it
   could not be audited from the local checkouts.

## Task 2 — Dependency coverage under Debian 12 LTS

### Runtime stack actually in use (from `debian/control` across the core
packages)

- **PHP**: `php-vitexsoftware-multiflexi-core` build-depends on `php-yaml`,
  `php-intl`, `php-simplexml`; runtime depends on
  `php-vitexsoftware-ease-core`, `php-vitexsoftware-ease-fluentpdo`,
  `php-json-schema`, `php-symfony-process`,
  `php-dragonmantank-cron-expression`. `source/install.rst` states "PHP 8.1
  or newer." Debian 12 (Bookworm) ships PHP **8.2** as the default archive
  package; Debian 13 (Trixie) ships PHP **8.4**. Composer constraints seen
  across repos range from `php: ">=8.1"` to `">=8.2"` — all satisfied by
  Bookworm's php8.2.
- **Database clients** (`multiflexi-database/debian/control`):
  `multiflexi-mysql` depends on `php-mysql`, `php-cakephp-phinx`,
  `dbconfig-mysql`; `multiflexi-pgsql` depends on `php-pgsql`,
  `dbconfig-pgsql`; `multiflexi-sqlite` depends on `php-sqlite3`, `sqlite3`,
  `dbconfig-sqlite3`. Bookworm ships MariaDB 10.11 and PostgreSQL 15 as the
  archive defaults matching these client packages.
- Packages like `php-vitexsoftware-*`, `php-json-schema`,
  `php-dragonmantank-cron-expression`, and `php-cakephp-phinx` are shipped
  from **VitexSoftware's own repository** (repo.vitexsoftware.com /
  repo.multiflexi.eu), not the Debian archive — Debian LTS sponsor coverage
  does not apply to them at all; their support horizon is whatever
  VitexSoftware's own CI keeps building, i.e. entirely within our control.

### Cross-check against Debian 12 LTS coverage (Debian LTS tracker /
`wiki.debian.org/LTS`, checked 2026-07-13, not from memory)

- Debian 12 "Bookworm" transitioned from the Debian Security Team to the
  Debian LTS Team on **2026-07-12** (confirmed via
  `debian.org/News/2026/20260712`), continuing security updates through
  **2028-06-30**.
- LTS-supported architectures for Bookworm: amd64, i386, arm64, armhf,
  ppc64el (ppc64el is new to LTS coverage this cycle). MultiFlexi packages
  are built/published for `amd64` only — no architecture-coverage risk.
- `php8.2` (the source package backing the `php-mysql`/`php-pgsql`/
  `php-sqlite3`/`php-yaml`/`php-intl`/`php-simplexml` binaries MultiFlexi
  depends on) has already received an LTS-cycle security update
  (`8.2.32-1~deb12u1`, DSA-5878-1) — confirms **active LTS coverage today**
  for the core PHP runtime.
- Debian's own LTS announcement explicitly states: *"A few packages are not
  covered by the Bookworm LTS support. You can figure out if a specific
  package is covered by installing the `debian-security-support` package."*
  There is no single browsable list of covered packages beyond that tool
  and the LTS mailing list — this is the authoritative live source, not a
  static page, so exact coverage for `mariadb-10.11`,
  `postgresql-15`/client libs, and `dbconfig-common` could not be
  individually confirmed from public web sources in this pass. These are
  high-traffic, widely-depended-upon packages with a strong historical
  track record of LTS sponsorship, but **this is flagged as uncertain
  rather than assumed** — see open item below.

### Flag: uncertain LTS coverage

- **Action item (not resolved in this pass):** run `apt install
  debian-security-support && check-support-status` on a Bookworm host (or
  ask on `debian-lts@lists.debian.org`) to get a definitive yes/no on
  `mariadb-10.11`, `postgresql-15`, and `dbconfig-common` LTS coverage.
  This is the real forcing function for any Debian 12 sunset decision — not
  the Bookworm-the-OS EOL date itself, which is a red herring (Bookworm is
  not EOL, it's in its LTS phase).

## Sources consulted

- `debian.org/News/2026/20260712` — Bookworm → LTS transition announcement.
- Debian LTS wiki (`wiki.debian.org/LTS`, `wiki.debian.org/LTS/Extended`).
- Web search results on php8.2 DSA-5878-1 (Debian Security Advisory /
  Tracker), confirming active php8.2 LTS security fixes.
- Local repo clones under `~/Projects/Multi/` (git state as of 2026-07-13).
