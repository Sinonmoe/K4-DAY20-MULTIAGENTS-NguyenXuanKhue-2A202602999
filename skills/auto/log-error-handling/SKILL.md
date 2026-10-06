---
name: log-error-handling
description: When parsing log files, ensure that error entries are correctly identified and structured in the output.
---
1. Read the log file and identify entries with levels of ERROR or CRITICAL, ignoring other levels.
2. Extract the timestamp and convert it to UTC, ensuring the correct format is used.
3. Capture the service name, error message, and exception details, ensuring that exceptions are logged as `null` if absent.
4. Count the occurrences of each error entry, including handling repeated messages correctly.
5. Structure the output JSON according to the specified schema, ensuring all required fields are present.
6. Validate the output file for correct structure and data types before finalizing.
7. Document the parsing logic and any assumptions made during the process for clarity and future reference.
