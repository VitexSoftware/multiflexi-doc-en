# MultiFlexi Documentation

![MultiFlexi Documentation](multiflexi-doc.svg)

[![Documentation Status](https://readthedocs.org/projects/multiflexi/badge/?version=latest)](https://multiflexi.readthedocs.io/en/latest/)
[![Build Status](https://jenkins.proxy.spojenet.cz/buildStatus/icon?job=Foregin%2Fmultiflexi-doc-en)](https://jenkins.proxy.spojenet.cz/job/Foregin/job/multiflexi-doc-en/)

English documentation for [MultiFlexi](https://multiflexi.eu) — a PHP-based task scheduling and automation framework for accounting and business system integrations.

**Read online:** https://multiflexi.readthedocs.io/en/latest/

## Contents

- **Getting Started** — quickstart, installation, first-run setup
- **Core Concepts** — system overview, data model, job lifecycle, credential management, execution architecture
- **How-To Guides** — adding companies, installing applications, creating run templates, scheduling jobs, assigning credentials, debugging
- **Integration Guides** — AbraFlexi, Pohoda, Zabbix, OpenTelemetry, Ansible, Kubernetes
- **Reference** — REST API, CLI commands, configuration, application schema, executors, actions
- **System Administration** — Docker deployment, systemd services, database maintenance, backup, upgrading
- **Development** — architecture, project structure, application development, testing, contributing

## Building Locally

### Prerequisites

```bash
sudo apt install python3-sphinx python3-shibuya-sphinx-theme
```

Or with pip:

```bash
pip install -r requirements.txt
```

### Build HTML

```bash
make html
# Output: build/html/index.html
```

### Build other formats

```bash
make epub    # EPUB e-book
make latex   # LaTeX (requires texlive)
make text    # Plain text
```

## Automatic Publishing

Every push to `main` triggers a rebuild on [ReadTheDocs](https://multiflexi.readthedocs.io/) via GitHub Actions.

## Debian Package

The documentation is also distributed as a Debian package (`multiflexi-doc`) that installs the built HTML to `/usr/share/doc/multiflexi/html/`.

```bash
# Build the .deb
dpkg-buildpackage -b --no-sign

# Install
sudo apt install ./multiflexi-doc_*.deb
# Browse at http://localhost/multiflexi-doc/  (requires Apache or Nginx)
```

Apache configuration is enabled automatically on install.
Nginx snippet is installed to `/usr/share/doc/multiflexi/multiflexi-doc.nginx`.

## Documentation Standards

See [AGENTS.md](AGENTS.md) for language, formatting, and content rules that apply to all contributions.

Key rules:
- English only; active voice; second person ("you")
- reStructuredText (`.rst`) for all source files
- Always specify language in code blocks
- Provide working, copy-paste-ready examples
- Only document released, implemented behaviour
- Cross-check app/credential-type field docs against the [canonical JSON schemas](https://github.com/VitexSoftware/php-vitexsoftware-multiflexi-core)

## Contributing

1. Edit the relevant `.rst` file under `source/`
2. Build locally and verify: `make html`
3. Commit and push — ReadTheDocs rebuilds automatically

## Related Projects

| Project | Description |
|---|---|
| [MultiFlexi](https://github.com/VitexSoftware/MultiFlexi) | Main web application |
| [multiflexi-cli](https://github.com/VitexSoftware/multiflexi-cli) | Command-line interface |
| [multiflexi-tui](https://github.com/VitexSoftware/multiflexi-tui) | Terminal UI |
| [php-vitexsoftware-multiflexi-core](https://github.com/VitexSoftware/php-vitexsoftware-multiflexi-core) | Core PHP library |
| [multiflexi-api](https://github.com/VitexSoftware/multiflexi-api) | REST API server |
