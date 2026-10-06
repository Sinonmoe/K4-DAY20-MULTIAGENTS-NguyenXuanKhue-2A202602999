---
name: enforce-data-formatting
description: When processing data, ensure that all values conform to specified formats and types.
---
1. Validate that monetary values are represented in the correct format (e.g., integers in cents).
2. Ensure that date and time values are formatted as specified (e.g., `YYYY-MM-DDTHH:MM:SSZ` for UTC).
3. Check that all string values are properly stripped of whitespace and standardized (e.g., uppercase for region names).
4. Confirm that any lists or dictionaries created from data contain the expected keys and types.
5. Implement error handling for data conversion processes to catch and log any issues.
6. Use assertions or validation checks to ensure that calculated values (e.g., sums, counts) match expected results.
7. Document any assumptions made about data formats in the code comments or documentation.
