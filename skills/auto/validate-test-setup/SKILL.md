---
name: validate-test-setup
description: When setting up a testing environment, ensure all necessary files and modules are correctly referenced and available.
---
1. Verify that all required modules are installed and accessible in the testing environment.
2. Ensure that the test files are named correctly and follow the naming conventions (e.g., `test_*.py`).
3. Check that the paths to the modules being tested are correct and that they can be imported without errors.
4. Confirm that the test files do not modify any original source files; only new test files should be created.
5. Run a preliminary test command (e.g., `pytest`) to check for import errors before executing full test suites.
6. If errors occur, review the error messages for clues about missing files or incorrect paths.
7. Document any changes made to the test setup in a changelog or comments for future reference.
