Invoice item dispatch (SaaS provisioning)
=========================================

A paid invoice may contain several items and every item can require its own
playbook (for example *MultiFlexi*, *NextCloud 1 GB*, *Mailbox 1 GB*). MultiFlexi
starts **one work item per matching invoice item**, retries a failed one and never
runs the same item twice for the same invoice.

Flow
----

1. AbraFlexi sends a change notification (webhook) to the *abraflexi-webhook-acceptor*.
2. When the invoice becomes settled (``zbyvaUhradit`` drops to zero) the acceptor stores a
   synthetic change with operation ``settled`` and the invoice items in
   ``changes_cache.items``.
3. The eventor reads the changes of every enabled *event source* and expands each change
   into **Tasks** (one per matching event rule, or one per matching item for
   ``fanout=item`` rules). The Task has an idempotency key, so a repeated delivery
   does not create a second one.
4. Each due Task starts a Job of the rule's RunTemplate. The Job outcome fulfils the
   Task or schedules a retry; a Task that runs out of attempts ends as ``failed``/``dead``.
5. The RunTemplate of the application *Semaphore Run* launches the Semaphore template,
   waits for it and returns its result as the exit code.

Event rule options
------------------

``item_filter``
    JSON object, every pair must match the item. ``{"cenik": "code:NEXTCLOUD1"}`` matches
    the item of the price-list entry NEXTCLOUD1 (the ``code:`` prefix is optional).
    Without a filter all items match.

``fanout``
    ``none`` (default) - one work item per change; ``item`` - one per matching item.

.. code-block:: bash

   multiflexi-cli event-rule:create --event_source_id 4 --evidence faktura-vydana \
       --operation settled --runtemplate_id 12 \
       --item_filter '{"cenik":"code:NEXTCLOUD1"}' --fanout item

Environment passed to the job (and to the playbook)
---------------------------------------------------

``EVENT_INVOICE_ID``
    AbraFlexi id of the invoice
``EVENT_ITEM_ID``
    id of the invoice item
``EVENT_ITEM_CODE``
    price-list code of the item (``code:`` removed)
``EVENT_ITEM_NAME``
    item name (shortened, control characters removed)
``EVENT_ITEM_QUANTITY``
    quantity
``EVENT_IDEMPOTENCY_KEY``
    stable key of this unit of work; use it to make the playbook idempotent

Values coming from an invoice are tenant data: identifiers are reduced to a safe
character set and the playbook should validate them again before use.

Several users on one MultiFlexi (multi-tenant)
----------------------------------------------

One MultiFlexi instance, one acceptor and one Semaphore can serve many users who each have
their own AbraFlexi company. Give every tenant their own *event source* limited to their
company with ``server_url`` and their own rules and RunTemplates:

.. code-block:: bash

   multiflexi-cli event-source:create --name "tenant A" --adapter_type abraflexi \
       --db_database abraflexiwebhookacceptor --db_username ... --db_password ... \
       --server_url https://abraflexi.example.com:5434/c/company_a

Without ``server_url`` a source sees the changes of **all** companies stored by the acceptor.
All tenants' hooks point to the same acceptor URL with ``?company=<code>``.

Acceptor settings for several companies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The acceptor reads the paid invoice and its items from AbraFlexi to detect the *settled*
state. It uses the server and the credentials from ``/etc/abraflexi-webhook-acceptor/.env``
and reads the invoice from the company that sent the change. Because the webhook address
is controlled by the caller, only the company name is taken from the request and it must be
listed in ``WHA_ALLOWED_COMPANIES``:

.. code-block:: ini

   ABRAFLEXI_URL=https://abraflexi.example.com:5434
   ABRAFLEXI_COMPANY=company_a
   WHA_ALLOWED_COMPANIES=company_a,company_b

List every company the acceptor serves, including the one in ``ABRAFLEXI_COMPANY``. Without
``WHA_ALLOWED_COMPANIES`` the acceptor works with the single company from the ``.env`` file.

Cursor and cache of an event source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cursor ``last_processed_id`` of an event source is compared with the change *version* of
its AbraFlexi company (``inversion``), not with the row id in the acceptor cache. Versions
of two companies overlap, so set the cursor of a new source to the current version of its
own company. A cursor that is too low replays the whole history of the company, including
other event rules and flows that react to it.

A processed change is removed from the acceptor cache by its own row id, so processing one
tenant never deletes unprocessed changes of another.

The eventor ships its own ``MultiFlexi\EventSource`` that implements this tenant scope. Its
autoloader is registered with priority over the older copy in ``php-vitexsoftware-multiflexi-core``,
so the tenant-aware class is the one that runs.

Event Tasks are started by the eventor in a second step after the changes are expanded.
Check them with ``multiflexi-cli task:list``; an open Task is started on the next cycle.
