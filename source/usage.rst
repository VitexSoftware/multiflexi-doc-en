Usage Guide
===========

.. toctree::
   :maxdepth: 2

.. contents::
   :local:

MultiFlexi provides a unified platform for scheduling, executing, and monitoring automated tasks. This guide covers the primary interfaces and common workflows.

Accessing MultiFlexi
--------------------

MultiFlexi offers three distinct interfaces for valid interaction:

1.  **Web Interface**: The primary dashboard for management and monitoring.
2.  **Command Line Interface (CLI)**: For server-side management and scripting.
3.  **API**: For programmatic integration.

Web Interface
-------------

The web interface is the central hub for MultiFlexi.

**Login**

Navigate to ``http://<your-server>/multiflexi`` and log in with your credentials.

**Dashboard Overview**

Upon login, the dashboard presents:

- **System Status**: Real-time health metrics.
- **Recent Jobs**: Status of recently executed tasks.
- **Upcoming Schedule**: Timeline of planned executions.

A welcome banner, quick-action buttons, and summary statistics stay at the top.
The detail sections below — **Recent Jobs**, **My Recent Activity Log**, **Account
Information**, and **RBAC Privileges & Access** — are grouped into a collapsible
accordion, with *Recent Jobs* expanded by default. Click a section header to
expand it; opening one collapses the others.

The same accordion pattern is used to organize other long pages: the **My
Profile** page groups Profile Information, Update Personal Information, Change
Password, GDPR rights, and recent data changes; and the **Cookie Policy** and
**Privacy Policy** pages collapse their numbered policy sections so you can jump
to the one you need.

**Common Actions**

- **Manage Companies**: Configure tenants (companies) that MultiFlexi will interact with.
- **Install Applications**: Browse and enable applications for specific companies.
- **Schedule Jobs**: Define when and how applications should run.
- **View Logs**: Inspect detailed execution history for debugging.

**Slide-in Panels**

Several parts of the interface use Bootstrap *offcanvas* drawers that slide in
from the side instead of taking the user to a new page:

- **Navigation drawer**: On small screens the top menu collapses into a hamburger
  button that opens the full navigation as a drawer sliding in from the left. On
  large screens the menu stays inline as usual.
- **Filters**: List pages (for example **Companies**) provide a *Filters* button
  that opens a drawer with search fields. Apply the filters to narrow the list, or
  use *Reset* to clear them.
- **Details**: Detail pages (for example a single **Company**) offer a *Details*
  button that opens a drawer with the full record at a glance, so you can inspect
  it without leaving the current view.
- **Help**: A floating ``?`` button in the lower-right corner opens a help drawer
  with links to the documentation, the About page, and the project source.

Click the close button, press *Esc*, or click outside the drawer to dismiss it.

Command Line Interface (CLI)
----------------------------

The ``multiflexi-cli`` tool allows for efficient system management directly from the terminal.

**Basic Usage**

.. code-block:: bash

   multiflexi-cli [command] [options]

**Key Commands**

- ``multiflexi-cli list``: List all registered jobs.
- ``multiflexi-cli run-template:schedule --id=<id>``: Manually trigger a specific job.
- ``multiflexi-cli status``: Check the health of the scheduler daemon.

For a complete command reference, see- :doc:`reference/cli`
- :doc:`reference/cli`
.

API Integration
---------------

MultiFlexi exposes a RESTful API for external integrations.

- **Endpoint**: ``/api/``
- **Authentication**: OAuth2 or API Tokens.
- **Format**: JSON, XML.

Developers should refer to the- :doc:`reference/api`
 documentation for endpoint details and usage examples.

Common Workflows
----------------

Creating a New Schedule
~~~~~~~~~~~~~~~~~~~~~~~

1.  **Select Company**: Choose the target company from the top menu.
2.  **Choose Application**: Navigate to "Applications" and select the tool to schedule.
3.  **Configure Job**:
    - Set parameters (dates, filters, etc.).
    - Define the **Interval** (e.g., Every Morning at 8:00 AM).
4.  **Save**: The job is now active and will run automatically.

Monitoring Execution
~~~~~~~~~~~~~~~~~~~~

1.  Go to **Job History**.
2.  Filter by Status (Success, Failed).
3.  Click **Log** on any entry to see the full output.

GDPR & Data Privacy
-------------------

MultiFlexi is designed with privacy in mind.

- **Data Retention**: Old transaction data is automatically pruned based on configured retention policies.
- **Right to Erasure**: Tools are available to anonymize or delete specific user data upon request.
- **Audit Trails**: All administrative actions are logged for compliance.

For detailed compliance procedures, consult :doc:`gdpr-compliance`.
