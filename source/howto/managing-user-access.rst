.. _howto-managing-user-access:

Managing User Access to Companies
==================================

This guide explains how to assign and revoke user access to companies in MultiFlexi using the Access Rights interface.

.. contents:: On This Page
   :local:
   :backlinks: none

---

Overview
--------

In MultiFlexi, access to companies (and all company-related resources like credentials and jobs) is controlled through the **Access Rights** feature. Users can only work with companies they are explicitly assigned to.

This guide covers:

- Granting access to a user
- Revoking access from a user
- Viewing all user assignments for a company
- Assigning a user to multiple companies

---

Prerequisites
-------------

- You must be logged in as an administrator
- The target company must exist
- The target user must exist in the system
- You need access to the company to manage its permissions

---

Granting Access to a User
--------------------------

Step 1: Navigate to the Company
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. In the MultiFlexi web UI, click **Companies**
2. Find and click on the company name
3. You should see the company details page

Step 2: Open Access Rights
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. On the company page, look for the **"Access Rights"** button
2. Click it to open the user assignment interface

Step 3: Find the User
~~~~~~~~~~~~~~~~~~~~~

The Access Rights page shows a table of all users in the system:

.. image:: /company-access-rights.png
   :alt: Company Access Rights Interface
   :align: center

Columns:

- **User** — Username (clickable link to user profile)
- **Email** — User's email address
- **Role** — Current role (currently all "viewer")
- **Assigned** — Toggle switch (currently off)

To find a specific user:

- Scroll through the list
- Or use the **Search Users** box at the top to filter by name or email

Step 4: Enable Access
~~~~~~~~~~~~~~~~~~~~~

1. Locate the user in the list
2. In the **Assigned** column, toggle the switch to **ON** (blue/enabled state)
3. The page sends the assignment to the server

Step 5: Verify Success
~~~~~~~~~~~~~~~~~~~~~~

- The toggle should turn blue (indicating enabled)
- User now has access to this company
- They'll see it in their company list on next login

**Example**: Grant access to John Smith for ACME Corp

1. Click Companies → ACME Corp
2. Click "Access Rights"
3. Search for "John" in the list
4. Toggle his "Assigned" switch to ON
5. John can now access ACME Corp

---

Revoking Access from a User
----------------------------

Step 1-2: Navigate and Open Access Rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same as granting access (see above)

Step 3: Find the User
~~~~~~~~~~~~~~~~~~~~~

Locate the user in the table

Step 4: Disable Access
~~~~~~~~~~~~~~~~~~~~~~

1. In the **Assigned** column, toggle the switch to **OFF** (gray/disabled state)
2. The page sends the revocation to the server

Step 5: Verify Success
~~~~~~~~~~~~~~~~~~~~~~

- The toggle should turn gray (indicating disabled)
- User immediately loses access to this company
- Company disappears from their company list on next login

**Example**: Remove John's access to ACME Corp

1. Click Companies → ACME Corp
2. Click "Access Rights"
3. Find John in the list
4. Toggle his "Assigned" switch to OFF
5. John can no longer access ACME Corp

---

Assigning a User to Multiple Companies
---------------------------------------

A single user can have access to multiple companies. To assign a user to multiple companies:

1. **Repeat the granting process** for each company
2. Navigate to each company's "Access Rights" page
3. Enable the same user for each one

**Example**: Grant John access to ACME, TechCorp, and DataSys

1. Company ACME → Access Rights → Toggle John ON
2. Company TechCorp → Access Rights → Toggle John ON
3. Company DataSys → Access Rights → Toggle John ON

Now John's company list shows three companies.

---

Viewing All Assignments for a Company
--------------------------------------

To see which users have access to a specific company:

1. Navigate to the company page
2. Click "Access Rights"
3. All users with toggle **ON** have access
4. All users with toggle **OFF** don't have access

The list is searchable, so you can quickly find a user and check their status.

---

Bulk Operations (Advanced)
---------------------------

For assigning multiple users at once, you can:

**Option 1: Use the Web Interface** (Recommended)

1. Navigate to each company's Access Rights page
2. Toggle users ON/OFF
3. (Fast if assigning 5-10 users to 1 company)

**Option 2: Direct Database** (Advanced)

For bulk operations, database admins can execute SQL:

.. code-block:: sql

   -- Assign users 5, 6, 7 to company 2
   INSERT INTO company_user (company_id, user_id, role) 
   VALUES 
     (2, 5, 'viewer'),
     (2, 6, 'viewer'),
     (2, 7, 'viewer');

   -- Remove user 5's access from all companies
   DELETE FROM company_user WHERE user_id = 5;

   -- Remove all users' access to company 2
   DELETE FROM company_user WHERE company_id = 2;

**Warning**: Direct database manipulation doesn't trigger UI updates. Use the web interface when possible.

---

Common Scenarios
----------------

Scenario 1: New Employee Joins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Steps:

1. Create user account (if not already created)
2. Navigate to each company they should access
3. Open Access Rights
4. Toggle their name ON

Scenario 2: Employee Changes Departments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Steps:

1. Navigate to their **old** company's Access Rights
2. Toggle their name OFF (revoke old access)
3. Navigate to their **new** company's Access Rights
4. Toggle their name ON (grant new access)

Scenario 3: Contractor Needs Temporary Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Steps:

1. Create contractor user account
2. Grant access to needed companies
3. When contract ends, navigate to each company and toggle them OFF
4. (Optionally delete contractor user account)

Scenario 4: Audit: Who Has Access to Sensitive Company?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Steps:

1. Navigate to the sensitive company page
2. Click "Access Rights"
3. Count all users with toggle ON
4. Review if that list is appropriate

---

Troubleshooting
---------------

"I Toggled ON but User Still Can't Access"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Causes**:

- User might be caching old session. Solution: Have them log out/in
- Browser might be caching the page. Solution: Refresh with Ctrl+F5
- Server might not have received the toggle. Solution: Try toggling again

"I Don't See a User in the List"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Causes**:

- User hasn't been created yet. Solution: Create the user first in the Users section
- Search filter is hiding them. Solution: Clear the search box
- User was deleted. Solution: You can't re-assign a deleted user

"Toggling ON/OFF Does Nothing"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Causes**:

- You might not have admin access to this company
- JavaScript is disabled in your browser
- Network error occurred

**Solutions**:

1. Check if you're logged in as admin
2. Check browser console for JavaScript errors (F12)
3. Try refreshing the page and toggling again
4. Check server logs for errors

---

Best Practices
--------------

✅ **Do**

- Review access rights regularly (monthly/quarterly)
- Remove access when users leave
- Document why users have access (in comments or tickets)
- Use the web interface for most operations
- Verify access was granted by logging in as the user

❌ **Don't**

- Grant access to all users "just in case"
- Forget to revoke access when users leave
- Use database manipulation for regular operations
- Assign users to companies they don't need

---

See Also
--------

- :ref:`concepts-rbac` — Understanding RBAC architecture and concepts
- :ref:`troubleshooting` — General troubleshooting guide
- User Management — How to create and manage user accounts

---

**Last Updated**: 2026-06-06  
**Version**: 1.0
