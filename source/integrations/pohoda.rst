Pohoda Integration
==================

`Stormware Pohoda <https://www.stormware.cz/pohoda/>`_ is a Czech accounting
and ERP system. MultiFlexi applications can integrate with Pohoda via its
XML/mServer interface.

.. contents::
   :local:
   :depth: 2

Overview
--------

Pohoda exposes a TCP/IP XML interface through its companion service
**mServer**. Applications send XML request documents and receive XML response
documents over a persistent connection. MultiFlexi provides the
``multiflexi-mserver`` credential type so that any application can reference
a Pohoda mServer endpoint without hardcoding connection details.

Installation
------------

.. code-block:: bash

   sudo apt install multiflexi-mserver

Credential Fields
-----------------

.. list-table::
   :header-rows: 1
   :widths: 30 55

   * - Variable
     - Description
   * - ``POHODA_HOST``
     - Hostname or IP address of the Pohoda mServer
   * - ``POHODA_PORT``
     - TCP port (default ``5336``)
   * - ``POHODA_ICO``
     - Company registration number (IČO) identifying the Pohoda company database
   * - ``POHODA_USERNAME``
     - Pohoda user login
   * - ``POHODA_PASSWORD``
     - Pohoda user password

Assigning the Credential to a RunTemplate
------------------------------------------

.. code-block:: bash

   multiflexi-cli run-template:assign-credential --id=<runtemplate_id> --credential_id=<credential_id>

Application Development
-----------------------

Applications that work with Pohoda data typically use the
`php-pohoda-connector <https://github.com/VitexSoftware/php-pohoda-connector>`_
library. Credential variables are injected as standard environment variables
into the job process:

.. code-block:: php

   $connector = new \Pohoda\Connector(
       getenv('POHODA_HOST'),
       (int) getenv('POHODA_PORT'),
       getenv('POHODA_ICO'),
       getenv('POHODA_USERNAME'),
       getenv('POHODA_PASSWORD')
   );

See Also
--------

- :doc:`/credential-type` — how credential types work in MultiFlexi
- :doc:`/concepts/credential-management` — credential architecture overview
- `Stormware Pohoda mServer documentation <https://www.stormware.cz/xml/>`_
