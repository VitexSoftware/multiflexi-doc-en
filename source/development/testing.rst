.. _testing:

Testing Strategy
----------------

MultiFlexi employs a comprehensive testing strategy to ensure code quality and system reliability:

**Unit Testing**
  PHPUnit tests for individual components and classes, focusing on business logic validation and error handling.

**Integration Testing**  
  Database connectivity testing and API endpoint validation across different environments.

**End-to-End Web Testing**
  Comprehensive Selenium-based web interface testing with support for multiple environments and internationalization. 
  See :doc:`/selenium-testing` for detailed information.

**Key Testing Features:**

- **Multi-Environment Support**: Testing across development, local package, and staging environments
- **International Standards**: Full English localization for global development teams  
- **Business Scenario Testing**: Real-world workflow validation including AbraFlexi integration
- **Automated CI/CD Integration**: Headless testing support for continuous integration pipelines

**Running Tests:**

.. code-block:: bash

    # PHP Unit Tests
    ./vendor/bin/phpunit
    
    # Static Analysis
    ./vendor/bin/phpstan analyse
    
    # Selenium Web Tests
    cd tests/selenium
    npm install
    npm run dev:simple        # Quick smoke test
    npm run test:scenarios    # Business scenarios
