# SBOM / CRA Compliance Audit — 2026-07

Raw findings behind `source/sbom-process.rst` and `source/cra-scope-notes.rst`.
Not part of the built documentation; kept for traceability of the reasoning
and data behind those pages. Audited from local clones under
`~/Projects/Multi/` plus a GitHub API sweep of the `VitexSoftware` and
`Spoje-NET` orgs, 2026-07-28.

## Method

- **Org-wide manifest presence** (all 278 repos: 201 VitexSoftware + 77
  Spoje-NET): `sbom-audit-tools/gh-manifest-scan.sh`, using `gh api
  repos/{org}/{repo}/git/trees/{branch}?recursive=1` (one call per repo, no
  cloning) and grepping the returned tree for `composer.json`,
  `composer.lock`, `package.json`, `package-lock.json`, `pyproject.toml`,
  `requirements.txt`, `go.mod`, `pom.xml`, `debian/control`, `Dockerfile*`.
  Raw output: `sbom-audit-tools/manifest-scan.csv`.
- **Local deep verification** (the ~40 repos actively cloned under
  `~/Projects/Multi/`, representing the maintained MultiFlexi product
  surface): `sbom-audit-tools/local-inventory.sh`, using `git ls-files` to
  confirm lockfile *commit* status (not just presence on disk) and to detect
  existing Dependabot/Renovate config. Raw output:
  `sbom-audit-tools/local-inventory.csv`.
- **SBOM generation**: `sbom-audit-tools/generate-sbom.sh` /
  `generate-sbom-all.sh`, dispatching to a CycloneDX generator per detected
  ecosystem (see `source/sbom-process.rst` for the tool table). Raw gap
  summary: `sbom-audit-tools/gap-summary.csv`.
- All scripts and generated SBOM files are kept in a local-only directory
  (`~/Projects/Multi/sbom-audit-tools/`), not committed to any repository,
  per the audit's guardrail against unreviewed cross-repo changes.

## Scope exclusions

- `multifymfo-old`, `MultiSymfo` — local clones with no git remote
  configured (orphaned/local-only artifacts, not tracked repos).
- `zabbix-agent2-plugin-multiflexi` — remote is `git.zabbix.com`, not
  VitexSoftware/Spoje-NET; it's a fork of a vendor example, not an
  org-owned product component.
- `jenkins-configuration`, `jenkins-multiflexi`, `MultiFlexi-cz`,
  `MultiFlexi-publish`, `multiflexi-buildimages`, `multiflexi-mtr` —
  Debian-packaging-only repos with no application-level dependency
  manifest. A `debian/control` Build-Depends-based SBOM is a distinct
  mechanism, deferred to a future phase (per explicit decision during this
  audit).

## Task 1 — Org-wide manifest inventory (summary)

278 repos scanned (201 VitexSoftware, 77 Spoje-NET); 193 have at least one
recognized dependency manifest. Ecosystem totals across both orgs:

| Ecosystem | Manifest file | Repo count |
|---|---|---|
| PHP / Composer | `composer.json` | 151 |
| Python | `pyproject.toml` | 22 |
| Python | `requirements.txt` | 21 |
| npm / Node | `package.json` | 11 |
| Java / Maven | `pom.xml` | 4 |
| Go | `go.mod` | 1 (locally cloned set has 2 — `multiflexi-tui` plus the excluded `zabbix-agent2-plugin-multiflexi`) |

Full per-repo detail: `sbom-audit-tools/manifest-scan.csv`.

This confirms PHP/Composer dominance at full-org scale, not just within the
locally cloned subset — validating `cyclonedx-php-composer` as the
highest-value single generator, while the other four ecosystems still
require their own tooling (see `source/sbom-process.rst`).

## Task 1 — Local repo inventory (lockfile + existing tooling)

40 locally cloned repos checked. Dependabot was the **only** pre-existing
dependency-alerting mechanism found anywhere (no Renovate, no SBOM tooling
of any kind), present on 9 repos: `multiflexi-cli`, `multiflexi-database`,
`multiflexi-doc-en`, `multiflexi.eu`, `multiflexi-executor`,
`multiflexi-scheduler`, `multiflexi-server`, `multiflexi-web`,
`php-vitexsoftware-multiflexi-core`.

Repos with a PHP/Composer manifest but **no `composer.lock` committed to
git** (may still have one present on disk, untracked — see the `gap-summary.csv`
notes column for which): `multiflexi-abraflexi`, `multiflexi-api`,
`multiflexi-database-connection`, `multiflexi-mail`,
`multiflexi-microsoft365`, `multiflexi-probe`, `multiflexi-raiffeisenbank`,
`multiflexi-server`, `multiflexi-vaultwarden`. `multiflexi-mserver` (Spoje-NET)
has no `composer.lock` on disk at all.

`multiflexi-node-app` has no lockfile at all (npm). `node-red-contrib-multiflexi`
has a `package-lock.json` present on disk but not committed to git.

Full per-repo detail: `sbom-audit-tools/local-inventory.csv`.

## Task 3/7 — SBOM generation results / gap summary

`generate-sbom-all.sh` run against all 40 local repos (2026-07-28). Result:
27 SBOM files generated across 26 repos (`multiflexi-api` produced two —
PHP and npm). Full detail: `sbom-audit-tools/gap-summary.csv`. Key gaps
(no SBOM could be generated, and why):

| Repo | Reason |
|---|---|
| `multiflexi-all` | No recognized ecosystem manifest (Debian meta-package) |
| `multiflexi-common` | Only `pyproject.toml`, no `requirements.txt` — `cyclonedx-py` has no direct PEP 621 support |
| `multiflexi-mcp-server` | Same as above |
| `python3-shibuya-sphinx-theme` | Same as above |
| `multiflexi-mserver` | No `composer.lock` on disk at all — `cyclonedx-php-composer` cannot generate without one |
| `multiflexi-node-app` | No `package-lock.json` committed — `cyclonedx-npm` requires a lockfile or `node_modules` |
| `multiflexi-zabbix-selenium` | No `package.json` at top level (only `debian/control`) |

Generated SBOM files themselves (`sbom-audit-tools/sbom/*.cdx.json`) are
kept locally and are not part of this repository — they are a point-in-time
audit artifact, regenerable at any time via `generate-sbom-all.sh`.

## Follow-ups (not fixed by this audit)

- The lockfile gaps above block accurate SBOM generation for the affected
  repos and should be fixed at the source (commit a lockfile) — this audit
  does not add or commit any lockfile to any repo; that's a per-repo
  decision for the maintainer.
- `cyclonedx-py` lacks PEP 621 (`pyproject.toml`-only) support in its
  current CLI form; worth re-checking for a newer release or an alternative
  tool (e.g. `pip-audit --format cyclonedx-json` against a resolved
  environment) if those three repos need coverage.
- CI wiring (`sbom-workflow.yml.example`) is a draft only; no repo has it
  adopted as of this audit.
