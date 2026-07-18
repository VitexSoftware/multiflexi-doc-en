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

Step 4: Install Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MultiFlexi is a modular platform. Core functionality is enhanced by installing applications.

To list available MultiFlexi applications:

.. code-block:: bash

    apt search multiflexi

To install the full suite of standard applications:

.. code-block:: bash

    sudo apt install multiflexi-all

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
