.. _contributing:

Contributing
------------

We welcome contributions from the community. To contribute, follow these steps:

1. **Fork the Repository**: Fork the MultiFlexi repository to your GitHub account.
2. **Create a Branch**: Create a new branch for your feature or bugfix.

   .. code-block:: bash

      git checkout -b feature-name

3. **Make Changes**: Make your changes and commit them with a descriptive message.

   .. code-block:: bash

      git commit -m "Description of the feature or fix"

4. **Push Changes**: Push your changes to your forked repository.

   .. code-block:: bash

      git push origin feature-name

5. **Create a Pull Request**: Open a pull request on the original repository.

Thank you for contributing to MultiFlexi!

Development Workflow
--------------------

**Git Workflow**

MultiFlexi uses a standard Git workflow with feature branches:

1. **Create Feature Branch**: Always create a new branch for features or fixes

   .. code-block:: bash

      git checkout -b feature/new-executor-type
      git checkout -b fix/job-timeout-issue

2. **Commit Guidelines**: Use conventional commit messages

   .. code-block:: bash

      git commit -m "feat: add Kubernetes executor support"
      git commit -m "fix: resolve infinite recursion in Docker executor"
      git commit -m "docs: update API documentation"

3. **Testing Before Push**: Always run tests before pushing

   .. code-block:: bash

      ./vendor/bin/phpunit
      ./vendor/bin/phpstan analyse

**CI/CD Pipeline**

The project uses Jenkins for continuous integration:

1. **Source Push**: Code pushed to GitHub triggers Jenkins build
2. **Package Build**: ``debian/Jenkinsfile`` creates .deb packages (~10 minutes)
3. **Unstable Repository**: Packages available at:
   - ``http://repo.vitexsoftware.cz/``
   - ``http://repo.vitexsoftware.com/``
4. **Release Process**: Manual Jenkins trigger using ``debian/Jenkinsfile-release``
5. **Production Repository**: Released packages at ``https://repo.multiflexi.eu/``

**Deployment Environments**

* **Development**: ``http://localhost/MultiFlexi/`` (source code)
* **Local Package**: ``http://localhost/multiflexi/`` (installed .deb)
* **Testing**: ``https://vyvojar.spoje.net/multiflexi/`` (CI packages)
* **Demo**: ``https://demo.multiflexi.eu/`` (Ansible deployed)
* **Production**:
  - ``https://multiflexi.vitexsoftware.com/``
  - ``https://multiflexi.spojenet.cz/``

Handling Multiple Database Types
--------------------------------

MultiFlexi supports multiple database types including MySQL, SQLite, PostgreSQL, MSSQL, and almost every PDO-capable database engine. When writing queries, you need to ensure compatibility with these databases.

Here is an example method ``todaysCond`` that generates a condition to fetch records for the current day, compatible with different database types:

.. code-block:: php

   public function todaysCond(string $column = 'begin'): string {
       $databaseType = $this->getPdo()->getAttribute(\PDO::ATTR_DRIVER_NAME);

       switch ($databaseType) {
           case 'mysql':
               $cond = ('DATE(' . $column . ') = CURDATE()');
               break;
           case 'sqlite':
               $cond = ("DATE(" . $column . ") = DATE('now')");
               break;
           case 'pgsql':
               $cond = ('DATE(' . $column . ') = CURRENT_DATE');
               break;
           case 'sqlsrv':
               $cond = ('CAST(' . $column . ' AS DATE) = CAST(GETDATE() AS DATE)');
               break;
           default:
               throw new \Exception('Unsupported database type ' . $databaseType);
       }

       return $cond;
   }

This method checks the database type and returns the appropriate condition for fetching records for the current day based on the specified column.

By following this approach, you can ensure that your queries are compatible with multiple database types, making your application more flexible and robust.

GDPR Compliance Development
---------------------------

When developing MultiFlexi features, developers must consider GDPR compliance requirements:

**Data Processing Considerations**

- Implement privacy by design principles
- Minimize data collection and processing
- Ensure lawful basis for all processing activities
- Document data flows and processing purposes

**Security Requirements**

- Use encryption for sensitive data (AES-256)
- Implement proper access controls and logging
- Follow secure coding practices
- Regular security assessments

**Data Retention Implementation**

.. code-block:: php

   // Example: Implementing retention-aware data processing
   class DataProcessor {
       public function processWithRetention($data, $retentionPeriod) {
           // Set retention metadata
           $data['retention_expires'] = date('Y-m-d', strtotime('+' . $retentionPeriod));
           
           // Process data
           $this->processData($data);
           
           // Log for audit trail
           $this->addStatusMessage('Data processed with retention: ' . $retentionPeriod, 'info');
       }
   }

**GDPR-Compliant Logging**

.. code-block:: php

   // Avoid logging personal data
   $this->addStatusMessage('User login successful for ID: ' . $userId, 'info');
   // Instead of: 'User ' . $email . ' logged in'
   
   // Use structured logging for audit trails
   $this->addStatusMessage([
       'event' => 'data_access',
       'user_id' => $userId,
       'resource' => $resourceType,
       'timestamp' => date('c')
   ], 'audit');

For complete GDPR compliance documentation, see :doc:`/gdpr-compliance`.

Coding Standards and Best Practices
------------------------------------

**PHP Standards**

MultiFlexi follows PSR-12 coding standards with additional project-specific conventions:

* **Classes**: PascalCase (``RunTemplate``, ``JobExecutor``)
* **Methods**: camelCase (``executeJob``, ``getCompanyList``)
* **Variables**: camelCase (``$companyId``, ``$jobResult``)
* **Constants**: SCREAMING_SNAKE_CASE (``DB_HOST``, ``DEFAULT_TIMEOUT``)
* **Database**: snake_case (``run_template``, ``company_id``)

**Documentation Requirements**

All public methods must include PHPDoc comments:

.. code-block:: php

   /**
    * Execute a job with the specified parameters
    *
    * @param int $jobId The job identifier
    * @param array $params Execution parameters
    * @return bool True on success, false on failure
    * @throws \Exception When job cannot be found
    */
   public function executeJob(int $jobId, array $params = []): bool

**Environment Configuration**

Use environment variables for configuration, with sensible defaults:

.. code-block:: php

   $logLevel = getenv('LOG_LEVEL') ?: 'info';
   $dbHost = getenv('DB_HOST') ?: 'localhost';

**Logging Best Practices**

Use the Ease logging framework with appropriate log levels:

.. code-block:: php

   $this->addStatusMessage('Job started', 'info');
   $this->addStatusMessage('Processing company: ' . $companyName, 'debug');
   $this->addStatusMessage('Job failed: ' . $error, 'error');

Application JSON Schema Validation
-----------------------------------

MultiFlexi enforces JSON schema validation for application definitions to ensure consistency and prevent configuration errors.

**Schema URL**: https://raw.githubusercontent.com/VitexSoftware/php-vitexsoftware-multiflexi-core/refs/heads/main/multiflexi.app.schema.json

**Validation Command**:

.. code-block:: bash

    multiflexi-cli application validate-json --json path/to/app.json

**Common Validation Errors**:

* **Invalid type values**: Environment variable types must be one of: ``string``, ``file-path``, ``email``, ``url``, ``integer``, ``float``, ``bool``, ``password``, ``set``, ``text``
* **Array vs Object**: Fields like ``topics``, ``requirements``, and ``artifacts`` must be arrays, not objects
* **Missing required fields**: All required fields in the schema must be present

**Example of correct environment variable definition**:

.. code-block:: json

    "environment": {
        "FORCE_EXITCODE": {
            "type": "integer",
            "description": "Force specific exit code",
            "defval": "0",
            "required": false
        }
    }
