AbraFlexi Integration
=====================

.. image:: ../_static/images/components/multiflexi-abraflexi.svg
   :width: 96px
   :align: right
   :alt: multiflexi-abraflexi

`AbraFlexi <https://www.abra.eu/flexi/>`_ is a Czech ERP system. The MultiFlexi
AbraFlexi integration adds a credential prototype that lets any MultiFlexi
application authenticate against an AbraFlexi server.

.. contents::
   :local:
   :depth: 2

Packages
--------

.. list-table::
   :header-rows: 1
   :widths: 35 30 35

   * - Package
     - Enhances
     - Provides
   * - ``multiflexi-abraflexi``
     - ``php-vitexsoftware-multiflexi-core``
     - Credential prototype with AbraFlexi URL, login, password and company
   * - ``multiflexi-abraflexi-ui``
     - ``multiflexi-web``
     - Web UI: connectivity test, auth check, company listing

Installation
------------

.. code-block:: bash

   sudo apt install multiflexi-abraflexi multiflexi-abraflexi-ui

Credential Fields
-----------------

After installing the package, the AbraFlexi credential type becomes available
in **Credentials → New credential** in the web UI.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``ABRAFLEXI_URL``
     - *(required)*
     - AbraFlexi server URI, e.g. ``https://demo.flexibee.eu:5434``
   * - ``ABRAFLEXI_LOGIN``
     - ``winstrom``
     - AbraFlexi user login
   * - ``ABRAFLEXI_PASSWORD``
     - ``winstrom``
     - AbraFlexi user password
   * - ``ABRAFLEXI_COMPANY``
     - ``demo``
     - Company database name on the AbraFlexi server

Assigning the Credential to a RunTemplate
------------------------------------------

.. code-block:: bash

   # List available credentials of the AbraFlexi type
   multiflexi-cli credential:list --type=abraflexi

   # Assign credential ID 3 to RunTemplate ID 12
   multiflexi-cli run-template:assign-credential --id=12 --credential_id=3

Web UI Features
---------------

The ``multiflexi-abraflexi-ui`` package adds a **Test connection** panel
to the credential form:

- **Connectivity test** — sends a request to ``/start`` on the server
- **SSL validation** — warns if the certificate is self-signed or expired
- **Authentication test** — verifies login/password via the AbraFlexi REST API
- **Company listing** — fetches the list of companies from the server
- **Company existence check** — confirms the configured company name exists

See Also
--------

- :doc:`/credential-type` — how credential types work in MultiFlexi
- :doc:`/howto/assigning-credentials` — step-by-step guide
- `AbraFlexi API documentation <https://www.flexibee.eu/api/dokumentace>`_
