Installation Guide
==================

.. toctree::
   :maxdepth: 2

MultiFlexi is designed for easy installation on Debian-based systems. It supports multiple database backends (MySQL, PostgreSQL, SQLite) to fit various deployment needs.

**Current Version: 1.29.0**

Start monitoring your infrastructure immediately with the new **MultiFlexi Probe** included in this release.

Supported Platforms
-------------------

**Debian 13 (Trixie)** is the recommended platform for new installs.
MultiFlexi packages are also published for Ubuntu 24.04 LTS, Ubuntu 22.04
LTS, and Debian 12 (Bookworm, build-maintained but no longer promoted for
new installs). See :doc:`platform-support` for the full support matrix,
including end-of-coverage dates and why Debian 11 and 14 are not supported.

Prerequisites
-------------

Before installing, ensure your system meets the following requirements:

- **Operating System**: A supported Debian or Ubuntu release.
- **Memory**: Minimum 2GB RAM (recommended for smooth database migrations).
- **Database**: MySQL/MariaDB, PostgreSQL, or SQLite.
- **Web Server**: Apache2 (recommended), Nginx, or compatible web server.
- **PHP**: PHP 8.1 or newer with extensions: ``intl``, ``mbstring``, ``xml``, ``curl``, ``mysql``/``pgsql``/``sqlite3``.

Installation Steps
------------------

Follow these steps to install MultiFlexi on your server.

Step 1: Configure Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, add the MultiFlexi repository to your system's package sources.

.. code-block:: bash

    # Update package lists
    sudo apt update
    
    # Install dependencies for repository management
    sudo apt install -y lsb-release apt-transport-https bzip2 ca-certificates curl

    # Add GPG key
    sudo curl -fsSL https://repo.multiflexi.eu/KEY.gpg -o /usr/share/keyrings/multiflexi-archive-keyring.gpg

    # Add repository source
    echo "deb [signed-by=/usr/share/keyrings/multiflexi-archive-keyring.gpg] https://repo.multiflexi.eu/ $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/multiflexi.list

    # Refresh package lists
    sudo apt update

Step 2: Install MultiFlexi
~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose the package corresponding to your preferred database backend.

**Option A: MySQL / MariaDB (Recommended for Production)**

.. code-block:: bash

    sudo apt install multiflexi-mysql

**Option B: SQLite (Testing / Development)**

.. code-block:: bash

    sudo apt install multiflexi-sqlite

.. note::
   
   PostgreSQL support is currently experimental (`multiflexi-postgresql`). 

Step 3: Database Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

During installation, the ``dbconfig-common`` tools will prompt you to configure the database.

1.  **Configure database for multiflexi?** -> Select **Yes**.
2.  **Password for the new user**: You can leave this blank to let the system generate a secure random password.

.. tip::

    Configuration settings are automatically saved to ``/etc/multiflexi/multiflexi.env``.

.. note::

   After the database backend package (``multiflexi-sqlite``, ``multiflexi-mysql``,
   or ``multiflexi-pgsql``) is configured, its post-install script automatically
   creates ``/etc/multiflexi/multiflexi.env`` from ``database.env`` if that file
   does not yet exist. This applies to all database backends and ensures
   ``multiflexi-cli`` can locate its configuration immediately without any manual
   copy step.

Step 3b: Credential Encryption Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``multiflexi-common`` (pulled in as a dependency of ``multiflexi-mysql`` /
``multiflexi-sqlite``) asks, via ``debconf``, how to set up the master key
used to encrypt stored credential secrets (passwords, API keys, tokens) at
rest:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Choice
     - Effect
   * - **Generate a random key automatically** (default)
     - A secure key is generated with ``openssl rand`` and written to
       ``ENCRYPTION_MASTER_KEY`` in ``/etc/multiflexi/multiflexi.env``.
       Recommended for production.
   * - **Enter my own key**
     - Prompts (password-style input, not echoed) for a key to use instead
       — for example to match an existing deployment or a key managed
       externally. Leaving this blank falls back to generating one.
   * - **Do not encrypt credentials (development only)**
     - Sets ``DATA_ENCRYPTION_ENABLED=false``. Credential secrets are then
       stored as plaintext in the database. Only appropriate for local
       development — never for a deployment holding real credentials.

.. warning::

   Back up ``ENCRYPTION_MASTER_KEY`` somewhere safe. If it is ever lost,
   credentials already encrypted with it become permanently unrecoverable.
   See :doc:`administration/backup-recovery`.

This prompt only runs once — on upgrade, or on any subsequent
``dpkg-reconfigure multiflexi-common``, it is skipped automatically if
either ``ENCRYPTION_MASTER_KEY`` or ``DATA_ENCRYPTION_ENABLED=false`` is
already present in ``/etc/multiflexi/multiflexi.env``, so an existing
choice (and any already-encrypted data) is never overwritten. To change
your choice later, run:

.. code-block:: bash

    sudo dpkg-reconfigure multiflexi-common

The web interface itself does not require ``ENCRYPTION_MASTER_KEY`` to be
set — it works whether encryption is configured or not. See
:doc:`reference/configuration` for the full list of encryption-related
environment variables and :doc:`concepts/credential-management` for how
redaction and encryption interact.

Step 4: Install Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MultiFlexi is a modular platform. Core functionality is enhanced by installing applications.

To list available MultiFlexi applications:

.. code-block:: bash

    apt search multiflexi

To install the full suite of standard applications:

.. code-block:: bash

    sudo apt install multiflexi-all

Nginx Configuration (Manual Step)
----------------------------------

The ``multiflexi-web`` package auto-configures itself on **Apache2** and
**lighttpd** during installation (a ``conf-available`` snippet is enabled
and the web server is restarted automatically). It does **not** do this for
Nginx - Nginx has no equivalent drop-in ``conf-available`` mechanism, so a
server block has to be added by hand.

MultiFlexi is a plain PHP application (individual ``.php`` scripts, not a
single front controller), served through PHP-FPM, with one exception: the
REST API under ``/multiflexi/api`` is a Slim-based application that does
route everything through a single ``index.php``. The example below reflects
both.

.. code-block:: nginx

    # Adjust server_name, the PHP-FPM socket, and TLS directives for your
    # environment. This assumes MultiFlexi is reachable at /multiflexi/
    # under an existing site - add these blocks inside your server {} block.

    location /multiflexi {
        alias /usr/share/multiflexi-web;
        index index.php;

        location ~ \.php$ {
            fastcgi_split_path_info ^(.+\.php)(/.+)$;
            fastcgi_pass unix:/run/php/php8.2-fpm.sock;
            fastcgi_index index.php;
            include fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $request_filename;
        }

        # Deny access to dotfiles (.user.ini, .htaccess - the latter is
        # unused by Nginx but should never be served either way).
        location ~ /\. {
            deny all;
        }
    }

    location /multiflexi/api {
        alias /usr/share/multiflexi-server/api;
        index index.php;

        # Front-controller: route anything that isn't a real file/dir
        # through index.php (mirrors the Apache mod_rewrite rule shipped
        # for this path).
        try_files $uri $uri/ /multiflexi/api/index.php?$query_string;

        location ~ \.php$ {
            fastcgi_split_path_info ^(.+\.php)(/.+)$;
            fastcgi_pass unix:/run/php/php8.2-fpm.sock;
            fastcgi_index index.php;
            include fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        }

        location ~ /\. {
            deny all;
        }
    }

.. note::

   Nginx has no equivalent of Apache's per-directory ``php_admin_value``
   directives, so ``open_basedir`` hardening for MultiFlexi is instead
   shipped as ``/usr/share/multiflexi-web/.user.ini``, which PHP-FPM picks
   up automatically regardless of which web server sits in front of it -
   no Nginx-side configuration is needed for that part. ``allow_url_fopen``
   is ``PHP_INI_SYSTEM`` and has no per-app equivalent under either web
   server; set it in the PHP-FPM pool's ``php.ini`` if you need to
   override it.

.. tip::

   Replace ``php8.2-fpm.sock`` with the PHP-FPM socket (or ``host:port``)
   actually in use on your system - check
   ``/etc/php/*/fpm/pool.d/*.conf`` for the ``listen`` directive, or run
   ``ls /run/php/``.

Post-Installation Verification
------------------------------

After installation, verify that MultiFlexi is running correctly.

1.  **Web Interface**: Open your browser and navigate to ``http://<your-server-ip>/multiflexi``. You should see the login screen.
2.  **Service Status**: Check system logs to ensure no errors occurred during startup.

    .. code-block:: bash
    
        journalctl -u apache2  # Or your web server service

Next Steps
----------

- Proceed to :doc:`firstrun` for initial configuration.
- Configure :doc:`credential-type` to connect your business systems.
