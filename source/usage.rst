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
- **Job History Graph**: A spiral of recent jobs, one pixel per job. It is a
  timeline running outwards: the oldest job shown is in the centre and the
  newest, brightest one at the outer end. Going back in time, jobs blend more
  and more into the background, so the past recedes into the distance like a
  tunnel, and as new jobs arrive the oldest drop out in the middle (green = success, red = failure,
  yellow = not runnable (exit code 127), purple = exception (255), grey =
  waiting). The same widget appears on the home page, company,
  company+application, application, RunTemplate, jobs list, and status pages,
  scoped to the current context.

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

**Home Page (Overview)**

The home page (``main.php``) uses the dark *Nocturne* theme, which applies to
the whole web interface. From top to bottom it shows:

- **Summary**: runs, success rate, failures and queued jobs for the last 30
  days. Waiting jobs do not count against the success rate.
- **Companies**: one card per company you can access, with its success rate,
  a success/failure bar and the run templates that failed most often. Each run
  template name links to that run template, shown with the name it was saved
  under. Click elsewhere on a card to open that company's page
  (``company.php``). The summary, charts and
  queue always cover all companies you can access.
- **Runs per day** and **Job history**: stacked bars of job states per day and
  the job history spiral described above, with counts per state.
- **Scheduled jobs queue**: upcoming jobs grouped by day. Use the interval
  buttons (all, hourly, daily, weekly, monthly) and the text box to narrow the
  list without reloading. The queue refreshes every minute and shows only
  companies you have access to.

**Company Page**

The company page (``company.php``) is laid out like the home page, scoped to
one company:

- **Header**: logo, name and the company's 30-day summary (runs, success rate,
  failures, queued), with a toolbar linking to the company's applications,
  credentials, jobs, wizard, access rights and setup, and a *Details* button
  that opens the company record in a side drawer (logo, name, slug, company ID,
  e-mail, enabled/set-up state, creation and update times, and settings as
  formatted JSON; empty values are not shown).
- **Applications**: one compact tile per assigned application showing the exit
  code of its last job (click it to open that job), a spinner while it runs and
  an hourglass when another run is waiting. Click the name to open the
  application in this company.
  Above the tiles, tag buttons (``AbraFlexi``, ``RaiffeisenBank``, ``Mail`` and
  so on, with the number of applications) filter the tiles by the application
  tags that the activation wizard uses. One click shows only that tag, a second
  click on it shows all again; hold Ctrl, Cmd or Shift while clicking to
  combine several tags. Tags used by a single application are not offered.
- **Runs per day** and **Job history**: the same charts as on the home page,
  limited to this company.
- **Recent jobs**: the 20 newest jobs, including scheduled ones. Use the
  buttons above the table to show all, successful, failed or unfinished jobs
  (``showOnly`` URL parameter). *Schedule* queues the run template again and
  *Cancel* withdraws a scheduled job.

**Filtering by Application Tags**

Applications declare tags in their definition (the ``tags`` array of the
``*.app.json`` file, for example ``Bank``, ``Statements`` or ``Pohoda``). The
**Jobs** (``jobs.php``), **Run templates** (``runtemplates.php``) and
**Tasks** (``tasks.php``) pages show an *Application tags* picker above the
list:

- With no tag picked, the list shows everything.
- Each tag you pick narrows the list to records of applications that have
  **all** picked tags. Tags are matched regardless of letter case.
- *Clear* removes the tag filter.

The selection is stored in the page address as ``apptags`` (for example
``jobs.php?filter=failed&apptags=Bank,Statements``), so you can bookmark or
share a filtered view. It combines with the other filters on the page, such as
the job state buttons on **Jobs** or the state buttons on **Tasks**. The tag filter
narrows the lists only: the job history chart on **Jobs** and the summary
cards and charts on **Tasks** still cover all applications.

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
- **Top bar order**: on large screens the bar shows the logo, the search box
  (with the area selector), the menu, and on the right the sign-off link and the
  language selector. On small screens the search box stays in the bar next to the
  hamburger button and the sign-off link and language selector are at the bottom
  of the drawer.
- **Filters**: List pages (for example **Companies**) provide a *Filters* button
  that opens a drawer with search fields. Apply the filters to narrow the list, or
  use *Reset* to clear them.
- **Details**: Detail pages (for example a single **Company**) offer a *Details*
  button that opens a drawer with the full record at a glance, so you can inspect
  it without leaving the current view.
- **Help**: A floating ``?`` button in the lower-right corner opens a help drawer
  with links to the documentation, the About page, and the project source.
  When the REST API is installed, the drawer also links to the current page's
  data in the API (HTML, JSON, XML, YAML and CSV).

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
