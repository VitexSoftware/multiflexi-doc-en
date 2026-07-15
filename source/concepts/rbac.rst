.. _concepts-rbac:

Role-Based Access Control (RBAC)
=================================

**Overview**: MultiFlexi implements company-level RBAC to ensure users only access companies and resources they are explicitly assigned to.

.. contents:: On This Page
   :local:
   :backlinks: none

---

What is RBAC?
-------------

**Role-Based Access Control (RBAC)** is a security mechanism that restricts access to system resources based on user assignments. In MultiFlexi, RBAC operates at the **company level**:

- Users are assigned to **specific companies**
- Users can only view and manage companies they're assigned to
- All company-related resources (credentials, jobs, templates) are automatically filtered
- Unauthorized access attempts are denied with user-friendly messages

**Access Decision**: "Is user X assigned to company Y?"

Core Principles
~~~~~~~~~~~~~~~

1. **Deny by Default** — Resources are inaccessible unless explicitly granted
2. **Company-Centric** — All access decisions revolve around company assignments
3. **Fail Secure** — No silent failures; denial is explicit and logged
4. **Transparent** — Users understand why access is denied

---

How RBAC Works
--------------

Database Schema
~~~~~~~~~~~~~~~

RBAC relies on the ``company_user`` junction table:

.. code-block:: sql

   CREATE TABLE `company_user` (
     `id` INT AUTO_INCREMENT PRIMARY KEY,
     `company_id` INT NOT NULL,
     `user_id` INT UNSIGNED NOT NULL,
     `role` VARCHAR(32) DEFAULT 'viewer',
     `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

     UNIQUE KEY `company_user_company_user_unique` 
       (`company_id`, `user_id`),

     FOREIGN KEY `company_user_company_must_exist` 
       (`company_id`) REFERENCES `company`(`id`) 
       ON DELETE CASCADE,
     FOREIGN KEY `company_user_user_must_exist` 
       (`user_id`) REFERENCES `user`(`id`) 
       ON DELETE CASCADE
   );

**Fields**:

- ``company_id`` — Which company
- ``user_id`` — Which user
- ``role`` — Access level (currently: "viewer"; future: viewer/editor/admin)
- ``created_at`` — When access was granted

**Example**: Assign user John (ID=5) to ACME Corp (ID=2)

.. code-block:: sql

   INSERT INTO company_user (company_id, user_id, role) 
   VALUES (2, 5, 'viewer');

Now user 5 can access company 2.

Access Check Flow
~~~~~~~~~~~~~~~~~

When a user navigates to a protected resource:

.. code-block:: text

   1. Page loads (e.g., company.php?id=2)
   2. User must be logged in (enforced by onlyForLogged())
   3. Page extracts resource ID (e.g., company_id=2)
   4. Page calls: CompanyAccessControl::enforceCompanyAccess(2)
   5. System queries:
      SELECT * FROM company_user 
      WHERE user_id=5 AND company_id=2
   
   6. Result:
      ✅ Row exists → Access granted, page loads
      ❌ No row → Access denied, error shown, user redirected

Protected Resources
~~~~~~~~~~~~~~~~~~~

RBAC protects the following resources:

**Company Details**
- View company information
- Modify company settings
- Assign applications
- Set environment variables
- Manage credentials
- Delete company
- Manage user access

**Credentials**
- View credential details
- Edit credential
- Clone credential

**Jobs**
- View job details
- View job logs

**Lists**
- Company list (filtered to show only accessible companies)
- Credential list (filtered to show only accessible credentials)
- Job list (filtered to show only jobs from accessible companies)

---

Access Control in Practice
--------------------------

Granting Access
~~~~~~~~~~~~~~~

1. **Log in as admin**
2. Navigate to the company: ``company.php?id=X``
3. Click the **"Access Rights"** button
4. Find the user in the list
5. Toggle the switch to **enable** access
6. User gains immediate access

Removing Access
~~~~~~~~~~~~~~~

1. Same as above, but toggle the switch to **disable** access
2. Access is immediately revoked

Viewing Assignments
~~~~~~~~~~~~~~~~~~~

To see which users have access to a company:

1. Visit the company page
2. Click **"Access Rights"**
3. See a table of all users with assignment toggles

User Perspective
~~~~~~~~~~~~~~~~

**User with Access**: Sees company in list, can view details, manage resources

**User without Access**: 
- Company doesn't appear in company list
- Direct URL access (e.g., ``company.php?id=5``) shows error:

  .. code-block:: text

     ⚠️ You do not have access to company "ACME Corp"

Cascading Access
~~~~~~~~~~~~~~~~

Access to resources cascades based on company assignment:

- **If user has access to company X**:
  - Can view credentials for company X ✅
  - Can view jobs for company X ✅
  - Can see run templates for company X ✅

- **If user does NOT have access to company X**:
  - Cannot view anything related to X ❌
  - Credentials are filtered from lists ❌
  - Jobs are filtered from lists ❌

---

Architecture
------------

Core Components
~~~~~~~~~~~~~~~

**CompanyAccessControl Class**
  Central enforcement engine. Static methods for all access decisions:

  .. code-block:: php

     // Check if user can access company
     if (CompanyAccessControl::currentUserCanAccessCompany($companyId)) {
       // User has access
     }

     // Enforce access (exits if denied)
     CompanyAccessControl::enforceCompanyAccess($companyId);

**Filtered Listers**
  Automatically filter data based on accessible companies:

  .. code-block:: php

     // Only shows credentials from accessible companies
     $lister = new FilteredCredentialLister();
     $credentials = $lister->listingQuery()->fetchAll();

**Protected Pages**
  All resource pages enforce access at the top:

  .. code-block:: php

     <?php
     require_once './init.php';
     WebPage::singleton()->onlyForLogged();  // Require login
     
     $companyId = WebPage::getRequestValue('id', 'int');
     
     // Enforce access
     CompanyAccessControl::enforceCompanyAccess($companyId);
     
     // If code reaches here, access is granted
     // Safe to proceed with company operations

Decision Flow Diagram
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   User Request
       ↓
   [ Logged in? ]
       ├─ No  → Redirect to login
       └─ Yes ↓
   [ Extract resource ID ]
       ↓
   [ Query company_user table ]
       ├─ Row found  → Grant access ✅
       └─ No row     → Deny access, show error ❌

---

Security Properties
-------------------

What RBAC Protects Against
~~~~~~~~~~~~~~~~~~~~~~~~~~~

✅ **Direct URL manipulation**
   - Can't bypass UI by changing URL: ``company.php?id=999``
   - Access is checked server-side, not client-side

✅ **Data leakage across companies**
   - List pages automatically filter data
   - No employee sees other company's credentials or jobs

✅ **Unauthorized modifications**
   - Can't edit settings for inaccessible companies
   - Can't delete inaccessible companies

✅ **Session hijacking**
   - Even if attacker knows another company's ID
   - They still need to be in the ``company_user`` table

What RBAC Does NOT Protect Against
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

❌ **Compromised database** — Attacker with database access can read everything

❌ **Weak passwords** — If admin password is compromised, attacker can modify all access

❌ **Unencrypted credentials** — RBAC controls *who* accesses credentials, not their encryption

❌ **Network eavesdropping** — Use HTTPS to protect data in transit

---

Multi-Company Users
-------------------

A single user can be assigned to multiple companies:

.. code-block:: sql

   -- User 5 (John) assigned to 3 companies
   INSERT INTO company_user VALUES 
     (NULL, 1, 5, 'viewer', NOW()),  -- ACME Corp
     (NULL, 3, 5, 'viewer', NOW()),  -- TechCorp
     (NULL, 7, 5, 'viewer', NOW());  -- DataSys

When John logs in:

1. Sees 3 companies in the company list
2. Can switch between them
3. Sees only credentials and jobs from those 3 companies
4. Cannot access companies 2, 4, 5, or 6

---

Administration
--------------

Bulk Operations
~~~~~~~~~~~~~~~

To assign a user to multiple companies:

.. code-block:: php

   $user = new User(5);  // John
   $companyUser = new CompanyUser();
   
   foreach ([1, 3, 7] as $companyId) {
       $companyUser->company = new Company($companyId);
       $companyUser->assignUser(5, 'viewer');
   }

Reporting
~~~~~~~~~

See all users with access to a company:

.. code-block:: sql

   SELECT u.login, u.firstname, u.lastname, cu.role, cu.created_at
   FROM company_user cu
   JOIN user u ON cu.user_id = u.id
   WHERE cu.company_id = 1
   ORDER BY cu.created_at DESC;

See all companies a user has access to:

.. code-block:: sql

   SELECT c.name, c.id, cu.role, cu.created_at
   FROM company_user cu
   JOIN company c ON cu.company_id = c.id
   WHERE cu.user_id = 5
   ORDER BY cu.created_at DESC;

---

Audit Logging
-------------

All RBAC-relevant events are recorded in the ``security_audit_log`` table by the
``SecurityAuditLogger``. Each record stores the acting user, client IP address,
user agent, a severity, and a JSON ``additional_data`` payload with the affected
identifiers.

Logged event types
~~~~~~~~~~~~~~~~~~~

``company_user_assigned``
   A user was granted access to a company. Logged automatically by
   ``CompanyUser::assignUser()``, so it covers both the **Access Rights** toggle
   and the self-assignment that happens when a user creates a new company.
   ``additional_data`` includes ``user_id``, ``company_id`` and ``role``.

``company_user_removed``
   A user's access to a company was revoked. Logged automatically by
   ``CompanyUser::removeUser()``. ``additional_data`` includes ``user_id`` and
   ``company_id``.

``role_assigned`` / ``role_removed``
   A system RBAC role was granted to or removed from a user (via the **Access
   Control (RBAC)** panel on the user page). Logged by ``RoleBasedAccessControl``.
   Only administrators may change roles; non-administrator attempts are rejected
   with a message and logged as ``access_denied``.

``access_denied``
   A user was denied access to a company, credential, or job. Logged centrally by
   ``CompanyAccessControl`` whenever an ``enforce*`` check fails, and when a
   non-administrator tries to modify roles. ``additional_data`` includes the
   requested URI.

Reviewing events
~~~~~~~~~~~~~~~~

Recent events can be reviewed through the logs interface or programmatically:

.. code-block:: php

   $events = $GLOBALS['securityAuditLogger']->getRecentEvents(24, null, 'company_user_assigned');

.. note::

   Audit logging is loosely coupled through ``$GLOBALS['securityAuditLogger']``.
   When security logging is disabled (``SECURITY_LOGGING_ENABLED``), assignment
   and enforcement still work; the events are simply not recorded.

---

Future Enhancements
-------------------

**Phase 2** (Planned):

- Role differentiation (viewer, editor, admin)
- Time-limited access grants
- Access request workflow
- Bulk import (CSV)

**Phase 3** (Planned):

- Permission inheritance from user groups
- Fine-grained permissions (can_view, can_edit, can_delete)
- Cross-company roles (global admin)

---

Troubleshooting
---------------

User Says: "I Don't See a Company I Should Have Access To"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Diagnosis**:

1. Verify user is logged in
2. Check if user is in ``company_user`` table:

   .. code-block:: sql

      SELECT * FROM company_user 
      WHERE user_id = 5 AND company_id = 2;

**Solution**:

- If no row exists, assign the user via "Access Rights" button
- If row exists, clear browser cache (might be stale)

User Says: "I Can Still Access a Company After I Should Have Lost Access"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Diagnosis**:

1. Check if row still exists in ``company_user`` table
2. Verify access was actually removed (toggle was clicked)

**Solution**:

- Session might be caching access. Have user log out and log back in.
- Clear any application-level caches

Page Shows "Access Denied" When It Shouldn't
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Diagnosis**:

1. Check if user is actually logged in: ``var_dump($_SESSION['user_id']);``
2. Check if user_id exists in ``user`` table
3. Check if company_user entry exists

**Solution**:

1. Log out and log back in
2. Check ``company_user`` table for correct assignments
3. Verify company exists (not deleted)

---

Relationship to system-wide RBAC roles
---------------------------------------

.. note::

   Everything above describes **company membership** (the ``company_user``
   table): which companies a user can see, with a simple per-company role
   (``viewer``/``manager``/``admin``). It is managed via
   ``POST /company/{companyId}/user/`` and ``DELETE
   /company/{companyId}/user/{userId}``.

   MultiFlexi separately has **system-wide RBAC roles** (``rbac_roles`` /
   ``rbac_user_roles``, e.g. ``super_admin``, ``admin``, ``editor``,
   ``user``, ``viewer``), assigned independently of company membership via
   ``multiflexi-cli user-role:set`` or ``POST /user/{userId}/roles/``. These
   are two distinct, independently maintained mechanisms — a user's
   system-wide role does not imply company access, and company membership
   does not grant any system-wide role.

See Also
--------

- :ref:`howto-managing-user-access` — How to manage who has access to which companies
- :doc:`credential-management` — How credentials are encrypted and protected
- :doc:`data-model` — Database schema overview
- :ref:`troubleshooting` — Common issues and solutions

---

**Last Updated**: 2026-06-06  
**Version**: 1.0
